# Local Build

## Requirements

Docker
S2I

## Building

We utilize s2i in order to build images locally without having to use a dockerfile.
Ensure that the docker daemon is running then use the provided script to keep things simple.

`sudo sh dev/s2i.sh <image_name> <tag>`

The image will then be available in your local docker repo under the image and tag you used.

## Launching

Running Puptoo is a bit more complicated as it requires kafka, zookeeper, and minio to be up and running. The provided docker-compose file can help with that.

**Kafka** is the message queue service that puptoo writes and listens to.  
**Zookeeper** is a required component for kafka.  
**Minio** is a local S3-like instance where files can be stored and used for downloads.

The `.env` file included in this repo allows you to configure minio. The main thing to check is that you have the data and config directories created under `/mnt` or whever you set those dirs.

`sudo docker-compose up`

## Launching the Full Stack

The `full-stack.yml` file stands up ingress, kafka, puptoo, minio, and inventory components so that the entire first bits of the platform pipeline can be tested. 

    cd dev && sudo docker-compose -f full-stack.yml up 

**NOTE**: The full stack expects you to have an ingress and inventory image available. See those projects for steps for building the images needed. It's also typical for puptoo to fail to start if it can't initially connect to kafka. If this happens, simply run `sudo docker-compose -f full-stack up -d pup` to have it attempt another startup.

## Launching the Test Stack

This docker-compose file is configured so that we can test PUP by itself with no other components outside of a producer and consumer so we can watch files go through the system. 

You will need minio prior to testing with an insights archive stored in it. The name of the file will be the `REQUEST_ID` env variable in test-stack.yml under `producer`

    cd dev && sudo docker-compose -f test-stack.yml up --build

Once the stack is stood up, it's likely you'll have to start PUP again due to some kafka readiness issues.

    sudo docker-compose -f test-stack.yml up -d pup

Now you can start the consumer which will begin consuming the `platform.inventory.host-ingress` topic where PUPTOO sends completed payloads.

    sudo docker-compose -f test-stack.yml up -d consumer

Finally you can start the producer, which will immediately send 100 copies of the archive you configured through the system.

    sudo docker-compose -f test-stack up -d producer

Consumer will begin logging the `elapsed_time` value to show how long it took for pup to process the archive. These times are very low given that this entire setup is local to the system. We expect some added lag once we introduce puptoo to the OSD environment due to cloud storage being used and that download time likely taking a bit longer.