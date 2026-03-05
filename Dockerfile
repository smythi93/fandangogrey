FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# libltdl-dev is for building graphviz

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    openssh-client \
    libltdl-dev \
    autopoint \
    texinfo \
    help2man \
    git \
    cmake \
    wget \
    gnupg \
    vim \
    htop \
    file \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Fandango
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY . /app
RUN python -m pip install --upgrade pip setuptools wheel build pytest
RUN python -m build && pip install dist/*.whl && pip install -e ".[test]"

# Install LLVM-20 for fcc
RUN rm -fr /app/fcc
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor | tee /usr/share/keyrings/llvm-archive-keyring.gpg > /dev/null
RUN echo "deb http://apt.llvm.org/noble/ llvm-toolchain-jammy-20 main" | tee /etc/apt/sources.list.d/llvm20.list
RUN apt update && apt install -y --no-install-recommends \
  clang-20 clang-tools-20 clang-20-doc libclang-common-20-dev libclang-20-dev \
  libclang1-20 clang-format-20 python3-clang-20 clang-tidy-20 libllvm20 \
  llvm-20 llvm-20-dev llvm-20-doc llvm-20-examples llvm-20-runtime libclang-rt-20-dev \
  libc++-20-dev libc++abi-20-dev
RUN update-alternatives --install \
    /usr/bin/llvm-config       llvm-config      /usr/bin/llvm-config-20  201 \
    --slave /usr/bin/llvm-ar           llvm-ar          /usr/bin/llvm-ar-20 \
    --slave /usr/bin/llvm-as           llvm-as          /usr/bin/llvm-as-20 \
    --slave /usr/bin/llvm-bcanalyzer   llvm-bcanalyzer  /usr/bin/llvm-bcanalyzer-20 \
    --slave /usr/bin/llvm-cov          llvm-cov         /usr/bin/llvm-cov-20 \
    --slave /usr/bin/llvm-diff         llvm-diff        /usr/bin/llvm-diff-20 \
    --slave /usr/bin/llvm-dis          llvm-dis         /usr/bin/llvm-dis-20 \
    --slave /usr/bin/llvm-dwarfdump    llvm-dwarfdump   /usr/bin/llvm-dwarfdump-20 \
    --slave /usr/bin/llvm-extract      llvm-extract     /usr/bin/llvm-extract-20 \
    --slave /usr/bin/llvm-link         llvm-link        /usr/bin/llvm-link-20 \
    --slave /usr/bin/llvm-mc           llvm-mc          /usr/bin/llvm-mc-20 \
    --slave /usr/bin/llvm-mcmarkup     llvm-mcmarkup    /usr/bin/llvm-mcmarkup-20 \
    --slave /usr/bin/llvm-nm           llvm-nm          /usr/bin/llvm-nm-20 \
    --slave /usr/bin/llvm-objdump      llvm-objdump     /usr/bin/llvm-objdump-20 \
    --slave /usr/bin/llvm-ranlib       llvm-ranlib      /usr/bin/llvm-ranlib-20 \
    --slave /usr/bin/llvm-readobj      llvm-readobj     /usr/bin/llvm-readobj-20 \
    --slave /usr/bin/llvm-rtdyld       llvm-rtdyld      /usr/bin/llvm-rtdyld-20 \
    --slave /usr/bin/llvm-size         llvm-size        /usr/bin/llvm-size-20 \
    --slave /usr/bin/llvm-stress       llvm-stress      /usr/bin/llvm-stress-20 \
    --slave /usr/bin/llvm-symbolizer   llvm-symbolizer  /usr/bin/llvm-symbolizer-20 \
    --slave /usr/bin/llvm-tblgen       llvm-tblgen      /usr/bin/llvm-tblgen-20 \
    --slave /usr/bin/clang             clang            /usr/bin/clang-20 \
    --slave /usr/bin/clang++           clang++          /usr/bin/clang++-20 \
    --slave /usr/bin/opt               opt              /usr/bin/opt-20 \
    --slave /usr/bin/llc               llc              /usr/bin/llc-20

# Install fcc
#RUN mkdir -p /root/.ssh
#COPY fcc_deploy_key /root/.ssh/id_rsa
#RUN chmod 600 /root/.ssh/id_rsa
#RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN make fcc SUDO=

# Run indefinitely.
CMD ["tail", "-f", "/dev/null"]

