#!/usr/bin/env bash

# Store call site and cd to PADTAI directory
prev_dir=$PWD
cd "$(dirname "$0")"

# Store PADTAI directory
padtai_dir=$PWD

echo -e "[+] Preparing installation...\n"
sudo apt-get update

# Install git
echo -e "\n[+] Installing git...\n"
sudo apt install git
if [ $? -eq 0 ]; then
    echo -e "\n[+] Git installed successfully.\n"
else
    echo -e "\n[!] Couldn't install git. Please install it manually."
    exit 1
fi

# Install SWI-Prolog
echo -e "[+] Installing SWI-Prolog...\n"
sudo apt-get install software-properties-common
if [ $? -ne 0 ]; then
    echo -e "\n[!] Unsupported OS. Please install SWI-Prolog manually."
    exit 1
fi
sudo apt-add-repository ppa:swi-prolog/stable
sudo apt-get update
sudo apt-get install swi-prolog
if [ $? -eq 0 ]; then
    echo -e "\n[+] SWI-Prolog installed successfully.\n"
else
    echo -e "\n[!] Unsupported OS. Please install SWI-Prolog manually."
    exit 1
fi

# Install Python dependencies
echo -e "[+] Installing Python dependencies...\n"
pip3 install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "\n[+] Python dependencies installed successfully.\n"
else
    echo -e "\n[!] Couldn't install Python dependencies. Please make sure Python is set up correctly and that you're using Python 3.10 or above."
    exit 1
fi

# Install NuWLS solver
echo -e "[+] Installing NuWLS...\n"
cd ~
mkdir nuwls
cd nuwls
wget https://maxsat-evaluations.github.io/2023/mse23-solver-src/anytime/NuWLS-c-2023.zip
unzip NuWLS-c-2023.zip
cd NuWLS-c-2023/code
make
if [ $? -ne 0 ]; then
    echo -e "\n[!] Couldn't install NuWLS. Please use default solver."
    exit 1
fi
cd ../bin
echo -e "\nexport PATH=\$PATH:$PWD" >> ~/.bashrc
if [ $? -ne 0 ]; then
    echo -e "\n[!] Couldn't add NuWLS to PATH. Please add it manually. NuWLS is at $PWD."
    exit 1
fi
cd ../..
rm NuWLS-c-2023.zip
cd $padtai_dir
echo -e "\n[+] NuWLS installed successfully."

# Install PADTAI
echo -e "\n[+] Installing PADTAI...\n"
pip3 install .
if [ $? -eq 0 ]; then
    echo -e "\n[+] PADTAI installed successfully.\n"
else
    echo -e "\n[!] Couldn't install PADTAI. Please install it manually."
    exit 1
fi

echo -e "[+] Finished setting up dependencies."

# Restore call site
cd $prev_dir

exec bash
