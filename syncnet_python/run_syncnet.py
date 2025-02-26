import time, pdb, argparse, subprocess, pickle, os, gzip, glob

from .SyncNetInstance import *

# ==================== PARSE ARGUMENT ====================

parser = argparse.ArgumentParser(description="SyncNet")
parser.add_argument('--initial_model', type=str, default="syncnet_python/data/syncnet_v2.model", help='Path to the pre-trained model.')
parser.add_argument('--batch_size', type=int, default=20, help='Batch size for processing.')
parser.add_argument('--vshift', type=int, default=15, help='Max shift for evaluation.')
parser.add_argument('--data_dir', type=str, default='syncnet_python/data/work', help='Base directory for data.')
parser.add_argument('--videofile', type=str, default='', help='Path to the input video file.')
parser.add_argument('--reference', type=str, default='', help='Reference string for output files.')
opt = parser.parse_args()

setattr(opt, 'avi_dir', os.path.join(opt.data_dir, 'pyavi'))
setattr(opt, 'tmp_dir', os.path.join(opt.data_dir, 'pytmp'))
setattr(opt, 'work_dir', os.path.join(opt.data_dir, 'pywork'))
setattr(opt, 'crop_dir', os.path.join(opt.data_dir, 'pycrop'))

# ==================== LOAD MODEL AND FILE LIST ====================

s = SyncNetInstance()

s.loadParameters(opt.initial_model)
print("Model %s loaded." % opt.initial_model)

flist = glob.glob(os.path.join(opt.crop_dir, opt.reference, '0*.avi'))
flist.sort()

# ==================== GET OFFSETS ====================

dists = []
for idx, fname in enumerate(flist):
    offset, conf, dist = s.evaluate(opt, videofile=fname)
    dists.append(dist)

# ==================== PRINT RESULTS TO FILE ====================

output_path = os.path.join(opt.work_dir, opt.reference, 'activesd.pckl')
os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure the output directory exists

with open(output_path, 'wb') as fil:
    pickle.dump(dists, fil)

print(f"Offsets saved to {output_path}")