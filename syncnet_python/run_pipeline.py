import sys, time, os, pdb, argparse, pickle, subprocess, glob, cv2
import numpy as np
from shutil import rmtree

import scenedetect
from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.stats_manager import StatsManager
from scenedetect.detectors import ContentDetector

from scipy.interpolate import interp1d
from scipy.io import wavfile
from scipy import signal
from device_config import DEVICE

from .detectors.s3fd import S3FD

# ========== PARSE ARGS ==========
parser = argparse.ArgumentParser(description = "FaceTracker")
parser.add_argument('--data_dir',       type=str, default='syncnet_python/data/work', help='Output directory')
parser.add_argument('--videofile',      type=str, default='',   help='Input video file')
parser.add_argument('--reference',      type=str, default='',   help='Video reference')
parser.add_argument('--facedet_scale',  type=float, default=0.25, help='Scale factor for face detection')
parser.add_argument('--crop_scale',     type=float, default=0.40, help='Scale bounding box')
parser.add_argument('--min_track',      type=int, default=100,  help='Minimum facetrack duration')
parser.add_argument('--frame_rate',     type=int, default=25,   help='Frame rate')
parser.add_argument('--num_failed_det', type=int, default=25,   help='Number of missed detections allowed before tracking is stopped')
parser.add_argument('--min_face_size',  type=int, default=100,  help='Minimum face size in pixels')
opt = parser.parse_args()

# Set additional paths
setattr(opt, 'avi_dir', os.path.join(opt.data_dir, 'pyavi'))
setattr(opt, 'tmp_dir', os.path.join(opt.data_dir, 'pytmp'))
setattr(opt, 'work_dir', os.path.join(opt.data_dir, 'pywork'))
setattr(opt, 'crop_dir', os.path.join(opt.data_dir, 'pycrop'))
setattr(opt, 'frames_dir', os.path.join(opt.data_dir, 'pyframes'))

# ========== IOU FUNCTION ==========
def bb_intersection_over_union(boxA, boxB):
  
  xA = max(boxA[0], boxB[0])
  yA = max(boxA[1], boxB[1])
  xB = min(boxA[2], boxB[2])
  yB = min(boxA[3], boxB[3])
 
  interArea = max(0, xB - xA) * max(0, yB - yA)
 
  boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
  boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
 
  iou = interArea / float(boxAArea + boxBArea - interArea)
 
  return iou

# ========== FACE TRACKING ==========
def track_shot(opt, scenefaces):

  iouThres  = 0.5   
  tracks    = []

  while True:
    track     = []
    for framefaces in scenefaces:
      for face in framefaces:
        if track == []:
          track.append(face)
          framefaces.remove(face)
        elif face['frame'] - track[-1]['frame'] <= opt.num_failed_det:
          iou = bb_intersection_over_union(face['bbox'], track[-1]['bbox'])
          if iou > iouThres:
            track.append(face)
            framefaces.remove(face)
            continue
        else:
          break

    if track == []:
      break
    elif len(track) > opt.min_track:
      
      framenum    = np.array([ f['frame'] for f in track ])
      bboxes      = np.array([np.array(f['bbox']) for f in track])

      frame_i   = np.arange(framenum[0], framenum[-1]+1)

      bboxes_i    = []
      for ij in range(0,4):
        interpfn  = interp1d(framenum, bboxes[:,ij])
        bboxes_i.append(interpfn(frame_i))
      bboxes_i  = np.stack(bboxes_i, axis=1)

      if max(np.mean(bboxes_i[:,2]-bboxes_i[:,0]), np.mean(bboxes_i[:,3]-bboxes_i[:,1])) > opt.min_face_size:
        tracks.append({'frame':frame_i,'bbox':bboxes_i})

  return tracks

# ========== VIDEO CROP AND SAVE ==========
def crop_video(opt, track, cropfile):

  flist = glob.glob(os.path.join(opt.frames_dir, opt.reference, '*.jpg'))
  flist.sort()

  fourcc = cv2.VideoWriter_fourcc(*'XVID')
  vOut = cv2.VideoWriter(cropfile + 't.avi', fourcc, opt.frame_rate, (224,224))

  dets = {'x':[], 'y':[], 's':[]}

  for det in track['bbox']:

    dets['s'].append(max((det[3]-det[1]),(det[2]-det[0]))/2) 
    dets['y'].append((det[1]+det[3])/2) 
    dets['x'].append((det[0]+det[2])/2) 
  
  dets['s'] = signal.medfilt(dets['s'], kernel_size=13)   
  dets['x'] = signal.medfilt(dets['x'], kernel_size=13)
  dets['y'] = signal.medfilt(dets['y'], kernel_size=13)

  for fidx, frame in enumerate(track['frame']):

    cs  = opt.crop_scale

    bs  = dets['s'][fidx] 
    bsi = int(bs*(1+2*cs)) 

    image = cv2.imread(flist[frame])
    
    frame_image = np.pad(image, ((bsi,bsi),(bsi,bsi),(0,0)), 'constant', constant_values=(110,110))
    my  = dets['y'][fidx]+bsi
    mx  = dets['x'][fidx]+bsi 

    face = frame_image[int(my-bs):int(my+bs*(1+2*cs)), int(mx-bs*(1+cs)):int(mx+bs*(1+cs))]
    
    vOut.write(cv2.resize(face, (224,224)))

  audiotmp    = os.path.join(opt.tmp_dir, opt.reference, 'audio.wav')
  audiostart  = (track['frame'][0])/opt.frame_rate
  audioend    = (track['frame'][-1]+1)/opt.frame_rate

  vOut.release()

  # ========== CROP AUDIO FILE ==========

  command = ("ffmpeg -y -i %s -ss %.3f -to %.3f %s" % (
      os.path.join(opt.avi_dir, opt.reference, 'audio.wav'),
      audiostart,
      audioend,
      audiotmp
  )) 
  output = subprocess.call(command, shell=True, stdout=None)

  if output != 0:
    pdb.set_trace()

  sample_rate, audio = wavfile.read(audiotmp)

  # ========== COMBINE AUDIO AND VIDEO FILES ==========

  command = ("ffmpeg -y -i %st.avi -i %s -c:v copy -c:a copy %s.avi" % (
      cropfile,
      audiotmp,
      cropfile
  ))
  output = subprocess.call(command, shell=True, stdout=None)

  if output != 0:
    pdb.set_trace()

  print('Written %s' % cropfile)

  os.remove(cropfile + 't.avi')

  print('Mean pos: x %.2f y %.2f s %.2f' % (
      np.mean(dets['x']),
      np.mean(dets['y']),
      np.mean(dets['s'])
  ))

  return {'track': track, 'proc_track': dets}

# ========== FACE DETECTION ==========
def inference_video(opt):

  DET = S3FD(device=DEVICE)

  flist = glob.glob(os.path.join(opt.frames_dir, opt.reference, '*.jpg'))
  flist.sort()

  dets = []
      
  for fidx, fname in enumerate(flist):

    start_time = time.time()
    
    image = cv2.imread(fname)

    image_np = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    bboxes = DET.detect_faces(image_np, conf_th=0.9, scales=[opt.facedet_scale])

    dets.append([])
    for bbox in bboxes:
      dets[-1].append({'frame':fidx, 'bbox':(bbox[:-1]).tolist(), 'conf':bbox[-1]})

    elapsed_time = time.time() - start_time

    print('%s-%05d; %d dets; %.2f Hz' % (
        os.path.join(opt.avi_dir, opt.reference, 'video.avi'),
        fidx,
        len(dets[-1]),
        (1 / elapsed_time) if elapsed_time > 0 else 0
    )) 

  savepath = os.path.join(opt.work_dir, opt.reference, 'faces.pckl')

  with open(savepath, 'wb') as fil:
    pickle.dump(dets, fil)

  return dets

# ========== SCENE DETECTION ==========
def scene_detect(opt):

  video_manager = VideoManager([os.path.join(opt.avi_dir, opt.reference, 'video.avi')])
  stats_manager = StatsManager()
  scene_manager = SceneManager(stats_manager)
  # Add ContentDetector algorithm (constructor takes detector options like threshold).
  scene_manager.add_detector(ContentDetector())
  base_timecode = video_manager.get_base_timecode()

  video_manager.set_downscale_factor()

  video_manager.start()

  scene_manager.detect_scenes(frame_source=video_manager)

  scene_list = scene_manager.get_scene_list(base_timecode)

  savepath = os.path.join(opt.work_dir, opt.reference, 'scene.pckl')

  if scene_list == []:
    scene_list = [(video_manager.get_base_timecode(), video_manager.get_current_timecode())]

  with open(savepath, 'wb') as fil:
    pickle.dump(scene_list, fil)

  print('%s - scenes detected %d' % (
      os.path.join(opt.avi_dir, opt.reference, 'video.avi'),
      len(scene_list)
  ))

  return scene_list
    

# ========== EXECUTE DEMO ==========
# ========== DELETE EXISTING DIRECTORIES ==========

def main():
    try:
        dirs_to_remove = [
            os.path.join(opt.work_dir, opt.reference),
            os.path.join(opt.crop_dir, opt.reference),
            os.path.join(opt.avi_dir, opt.reference),
            os.path.join(opt.frames_dir, opt.reference),
            os.path.join(opt.tmp_dir, opt.reference)
        ]

        for directory in dirs_to_remove:
            if os.path.exists(directory):
                rmtree(directory)

        # ========== MAKE NEW DIRECTORIES ==========
        dirs_to_create = [
            os.path.join(opt.work_dir, opt.reference),
            os.path.join(opt.crop_dir, opt.reference),
            os.path.join(opt.avi_dir, opt.reference),
            os.path.join(opt.frames_dir, opt.reference),
            os.path.join(opt.tmp_dir, opt.reference)
        ]

        for directory in dirs_to_create:
            os.makedirs(directory, exist_ok=True)

        # ========== CONVERT VIDEO AND EXTRACT FRAMES ==========
        video_output = os.path.join(opt.avi_dir, opt.reference, 'video.avi')
        command = ("ffmpeg -y -i %s -qscale:v 2 -async 1 -r 25 %s" % (
            opt.videofile,
            video_output
        ))
        output = subprocess.call(command, shell=True, stdout=None)

        frames_output = os.path.join(opt.frames_dir, opt.reference, '%06d.jpg')
        command = ("ffmpeg -y -i %s -qscale:v 2 -threads 1 -f image2 %s" % (
            video_output,
            frames_output
        )) 
        output = subprocess.call(command, shell=True, stdout=None)

        audio_output = os.path.join(opt.avi_dir, opt.reference, 'audio.wav')
        command = ("ffmpeg -y -i %s -ac 1 -vn -acodec pcm_s16le -ar 16000 %s" % (
            video_output,
            audio_output
        )) 
        output = subprocess.call(command, shell=True, stdout=None)

        # ========== FACE DETECTION ==========
        faces = inference_video(opt)

        # ========== SCENE DETECTION ==========
        scene = scene_detect(opt)

        # ========== FACE TRACKING ==========
        alltracks = []
        vidtracks = []

        for shot in scene:

            if shot[1].frame_num - shot[0].frame_num >= opt.min_track :
                alltracks.extend(track_shot(opt, faces[shot[0].frame_num:shot[1].frame_num]))

        # ========== FACE TRACK CROP ==========
        for ii, track in enumerate(alltracks):
            cropfile = os.path.join(opt.crop_dir, opt.reference, '%05d' % ii)
            vidtracks.append(crop_video(opt, track, cropfile))

        # ========== SAVE RESULTS ==========
        savepath = os.path.join(opt.work_dir, opt.reference, 'tracks.pckl')

        with open(savepath, 'wb') as fil:
            pickle.dump(vidtracks, fil)

        # Clean up temporary directory
        rmtree(os.path.join(opt.tmp_dir, opt.reference))

    except Exception as e:
        print(f"An error occurred during video processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()