python main.py -i ~/win_img/larmor/data/ -o ~/temp/c1 -s --convert
python main.py -i ~/win_img/larmor/data/ -o ~/temp/c1s -s --convert --data-as-stack
python main.py -i ~/win_img/larmor/data/ -o ~/temp/c2s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --out-format nxs --data-as-stack
python main.py -i ~/temp/c1s/pre_processed/ -o ~/temp/c2s2 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --out-format nxs --data-as-stack
python main.py -i ~/temp/c2s/pre_processed/ -o ~/temp/c3 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --in-format nxs
python main.py -i ~/temp/c2s/pre_processed/ -o ~/temp/c3s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --in-format nxs --data-as-stack
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/c4 -s --convert --out-format tiff 
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/c4s -s --convert --out-format tiff --data-as-stack
python main.py -i ~/temp/c1s/pre_processed/ -o ~/temp/c42 -s --convert --out-format tiff
python main.py -i ~/temp/c1s/pre_processed/ -o ~/temp/c4s2 -s --convert --out-format tiff --data-as-stack
python main.py -i ~/temp/c4/pre_processed/ -o ~/temp/c5 -s --convert --in-format tiff
python main.py -i ~/temp/c4/pre_processed/ -o ~/temp/c5s -s --convert --data-as-stack --in-format tiff
python main.py -i ~/temp/c4s/pre_processed/ -o ~/temp/c52 -s --convert --in-format tiff
python main.py -i ~/temp/c4/pre_processed/ -o ~/temp/c5s2 -s --convert --in-format tiff
python main.py -i ~/temp/c4/pre_processed/ -D ~/win_img/larmor/dark -F ~/win_img/larmor/flat -o ~/temp/c6s -s --convert --in-format tiff --out-format nxs --data-as-stack
python main.py -i ~/temp/c4s/pre_processed/-D ~/win_img/larmor/dark -F ~/win_img/larmor/flat  -o ~/temp/c6s2 -s --convert --in-format tiff --out-format nxs --data-as-stack
python main.py -i ~/temp/c6s/pre_processed/ -o ~/temp/c7 -s --convert --in-format nxs --out-format tiff
python main.py -i ~/temp/c6s/pre_processed/ -o ~/temp/c7 -s --convert --in-format nxs --out-format tiff --data-as-stack
python main.py -i ~/win_img/larmor/data/ -o ~/temp/p1 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc
python main.py -i ~/win_img/larmor/data/ -o ~/temp/p2 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc --data-as-stack
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/p3 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/p4 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc --data-as-stack
python main.py -i ~/temp/c2s2/pre_processed/ --only-preproc -o ~/temp/p42/ --in-format nxs --pre-median-size 3 -s
python main.py -i ~/temp/c2s2/pre_processed/ --only-preproc -o ~/temp/p43/ --in-format nxs --pre-median-size 3 -s --data-as-stack
python main.py -i ~/win_img/larmor/data/ -o ~/temp/c2s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --only-preproc --out-format nxs --data-as-stack --pre-median-size 3
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/p7 -D ~/win_img/777cannon/dark_cannon/ -F ~/win_img/777cannon/flat_cannon/ -s --only-preproc --in-format tif --pre-median-size 3
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/p7s -D ~/win_img/777cannon/dark_cannon/ -F ~/win_img/777cannon/flat_cannon/ -s --only-preproc --in-format tif --pre-median-size 3 --data-as-stack
