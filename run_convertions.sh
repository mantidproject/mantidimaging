python main.py -i ~/win_img/larmor/data/ -o ~/temp/c1s -s --convert --data-as-stack
python main.py -i ~/win_img/larmor/data/ -o ~/temp/c1 -s --convert
python main.py -i ~/win_img/larmor/data/ -o ~/temp/c2s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --out-format nxs --data-as-stack
python main.py -i ~/temp/c1s/pre_processed/ -o ~/temp/c2s2 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --out-format nxs --data-as-stack
python main.py -i ~/temp/c2s/pre_processed/ -o ~/temp/c3 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --in-format nxs
python main.py -i ~/temp/c2s/pre_processed/ -o ~/temp/c3s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --convert --in-format nxs --data-as-stack
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/c4 -s --convert --in-format tif
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/c4s -s --convert --data-as-stack --in-format tif
python main.py -i ~/win_img/larmor/data/ -o ~/temp/p1 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc
python main.py -i ~/win_img/larmor/data/ -o ~/temp/p2s -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc --data-as-stack
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/p3 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc
python main.py -i ~/temp/c1/pre_processed/ -o ~/temp/p4 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --pre-median-size 3 --only-preproc --data-as-stack
python main.py -i ~/temp/c2s2/pre_processed/ --only-preproc -o ~/temp/p6/ --in-format nxs --pre-median-size 3 -s
python main.py -i ~/temp/c2s2/pre_processed/ --only-preproc -o ~/temp/p6s/ --in-format nxs --pre-median-size 3 -s --data-as-stack
python main.py -i ~/win_img/larmor/data/ -o ~/temp/p2s2 -D ~/win_img/larmor/dark/ -F ~/win_img/larmor/flat/ -s --only-preproc --out-format nxs --data-as-stack --pre-median-size 3
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/p7 -D ~/win_img/777cannon/dark_cannon/ -F ~/win_img/777cannon/flat_cannon/ -s --only-preproc --in-format tif --pre-median-size 3
python main.py -i ~/win_img/777cannon/data/ -o ~/temp/p7s -D ~/win_img/777cannon/dark_cannon/ -F ~/win_img/777cannon/flat_cannon/ -s --only-preproc --in-format tif --pre-median-size 3 --data-as-stack