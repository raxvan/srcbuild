# Use the official Emscripten Docker image
FROM emscripten/emsdk:latest

RUN apt-get update && apt-get install -y \
    python3 \
    cmake

ENV EMSDK /emsdk
ENV PATH ${EMSDK}/upstream/emscripten:${PATH}

WORKDIR /wasmbuild

COPY . .

