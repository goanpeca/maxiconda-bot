#!/usr/bin/env bash

# Copyright (c) Semi-ATE
# Distributed under the terms of the MIT License

set -ex

# Check parameters
ARCH=${ARCH:-aarch64}
DOCKER_ARCH=${DOCKER_ARCH:-arm64v8}
DOCKERIMAGE=${DOCKERIMAGE:-condaforge/linux-anvil-aarch64}


#export CONSTRUCT_ROOT=/construct

echo "============= Create build directory ============="
mkdir -p build/
chmod 777 build/

echo "============= Enable QEMU in persistent mode ============="
docker run --rm --privileged multiarch/qemu-user-static --reset --credential yes --persistent yes

echo "============= Solve for Linux/${ARCH} ============="
docker run --rm -v "$(pwd):/construct" -e CONSTRUCT_ROOT -e MAXICONDA_VERSION -e MAXICONDA_NAME ${DOCKERIMAGE} /construct/scripts/build.sh
