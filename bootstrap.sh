#!/bin/sh
set -e

cd ~
if [ ! -f ".ingestBootstrapped" ]; then
    sudo apt update
    sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev


    curl -O https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tar.xz
    tar -xf Python-3.8.3.tar.xz
    cd Python-3.8.3
    ./configure --enable-optimizations
    make -j $(nproc)
    sudo make altinstall

    sudo mkdir -p /usr/local/bin/data_ingestion/
    python3.8 -m venv ~/venv
    ~/venv/bin/pip install --upgrade pip

    echo '# activate the virtual environment' >> ~/.bashrc
    echo 'source ~/venv/bin/activate' >> ~/.bashrc
    touch ~/.ingestBootstrapped
fi