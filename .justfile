set shell := ["bash", "-c"]

build:
  sudo docker build -t subz:subz .

subtitle target model="large-v3" audio-track="0" offset="0.0":
  REALPATH=$(realpath "{{target}}"); \
  BASENAME=$(basename "{{target}}"); \
  SRT_FILE=./${BASENAME}.srt;\
  touch ${SRT_FILE};\
  sudo docker run \
    -v ${HOME}/.cache/huggingface:/root/.cache/huggingface \
    -v ${HOME}/.cache/torch:/root/.cache/torch \
    -v ${REALPATH}:/app/${BASENAME} \
    -v ${SRT_FILE}:/app/${SRT_FILE} \
    --gpus all  \
    -it  \
    --rm  \
    subz:subz \
    python3 -W ignore main.py ${BASENAME} \
      --output ${SRT_FILE} \
      --whisper-model {{model}} \
      --audio-track {{audio-track}} \
      --offset {{offset}} > /dev/null; \
  echo "Subtitles saved at '${SRT_FILE}'"
