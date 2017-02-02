# fits - fits
python main.py -i ~/win_img/larmor/data/ -o ~/temp/f -s --convert
# fits - stack fits
python main.py -i ~/win_img/larmor/data/ -o ~/temp/fs -s --convert --data-as-stack

# fits - tiff
python main.py -i ~/win_img/larmor/data/ -o ~/temp/t -s --convert --out-format tif
# fits - stack tiff
python main.py -i ~/win_img/larmor/data/ -o ~/temp/ts -s --convert --data-as-stack --out-format tif

# fits - nxs
python main.py -i ~/win_img/larmor/data/ -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -o ~/temp/nxs -s --convert --data-as-stack --out-format nxs

# repeat same, but with stack of fits from ~/temp/fs/pre_processed
# stack fits - fits
python main.py -i ~/temp/fs/pre_processed -o ~/temp/f1 -s --convert
# stack fits - stack fits
python main.py -i ~/temp/fs/pre_processed -o ~/temp/fs1 -s --convert --data-as-stack

# stack fits - tiff
python main.py -i ~/temp/fs/pre_processed -o ~/temp/t1 -s --convert --out-format tif
# stack fits - stack tiff
python main.py -i ~/temp/fs/pre_processed -o ~/temp/ts1 -s --convert --data-as-stack --out-format tif

# stack fits - nxs
python main.py -i ~/temp/fs/pre_processed -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -o ~/temp/nxs1 -s --convert --data-as-stack --out-format nxs

# now start tiff to everything else
# tiff - fits
python main.py -i ~/temp/t1/pre_processed -o ~/temp/f2 -s --convert --in-format tiff
# tiff - stack fits
python main.py -i ~/temp/t1/pre_processed -o ~/temp/fs2 -s --convert --data-as-stack --in-format tiff

# tiff - tiff
python main.py -i ~/temp/t1/pre_processed -o ~/temp/t2 -s --convert --out-format tiff --in-format tiff
# tiff - stack tiff
python main.py -i ~/temp/t1/pre_processed -o ~/temp/ts2 -s --convert --data-as-stack --out-format tiff --in-format tiff

# need to convert flat and dark also
python main.py -i ~/win_img/larmor/dark/ -o ~/temp/tiff_dark -s --convert --out-format tiff
python main.py -i ~/win_img/larmor/flat/ -o ~/temp/tiff_flat -s --convert --out-format tiff
# stack tiff - nxs
python main.py -i ~/temp/t1/pre_processed -D ~/temp/tiff_dark/pre_processed -F ~/temp/tiff_flat/pre_processed -o ~/temp/nxs2 -s --convert --data-as-stack --out-format nxs --in-format tiff

# now stack of tiffs to everything else
# stack tiff - fits
python main.py -i ~/temp/ts1/pre_processed -o ~/temp/f3 -s --convert --in-format tiff
# stack tiff - stack fits
python main.py -i ~/temp/ts1/pre_processed -o ~/temp/fs3 -s --convert --data-as-stack --in-format tiff

# stack tiff - tiff
python main.py -i ~/temp/ts1/pre_processed -o ~/temp/t3 -s --convert --out-format tiff --in-format tiff
# stack tiff - stack tiff
python main.py -i ~/temp/ts1/pre_processed -o ~/temp/ts3 -s --convert --data-as-stack --out-format tiff --in-format tiff

# stack tiff - nxs
python main.py -i ~/temp/ts1/pre_processed -D ~/temp/tiff_dark/pre_processed -F ~/temp/tiff_flat/pre_processed -o ~/temp/nxs3 -s --convert --data-as-stack --out-format nxs --in-format tiff

# now for the last, unpack the nxs to everything else
# nxs - fits
python main.py -i ~/temp/nxs3/pre_processed -o ~/temp/f4 -s --convert --in-format nxs
# nxs - stack fits
python main.py -i ~/temp/nxs3/pre_processed -o ~/temp/f4s -s --convert --in-format nxs --data-as-stack

# nxs - tiff
python main.py -i ~/temp/nxs3/pre_processed -o ~/temp/f4 -s --convert --in-format nxs --out-format tiff
# nxs - stack tiff
python main.py -i ~/temp/nxs3/pre_processed -o ~/temp/f4s -s --convert --in-format nxs --data-as-stack --out-format tiff

# nxs - nxs
python main.py -i ~/temp/nxs3/pre_processed -D ~/temp/tiff_dark/pre_processed -F ~/temp/tiff_flat/pre_processed -o ~/temp/nxs4 -s --convert --data-as-stack --out-format nxs --in-format nxs
