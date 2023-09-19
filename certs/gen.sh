#!/bin/sh

COMMON_NAME=$1
SUBJECT="/C=CA/ST=None/L=NB/O=None/CN=$COMMON_NAME"
NUM_OF_DAYS=3650

openssl req -nodes -x509 -sha256 -newkey rsa:4096 \
  -key certs/cert.key \
  -CA certs/ca.crt \
  -CAkey certs/ca.key \
  -days $NUM_OF_DAYS \
  -subj $SUBJECT  \
  -addext "subjectAltName = DNS:localhost,DNS:$COMMON_NAME" 
