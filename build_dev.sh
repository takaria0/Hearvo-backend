docker-compose -f docker-compose.dev.yml build --force-rm 
docker-compose -f docker-compose.dev.yml up

# docker build --tag edu_dev:0.1 . -f Dockerfile.dev
# docker run --publish 5000:5000 edu_dev:0.1