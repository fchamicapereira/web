FROM ubuntu:jammy

# https://stackoverflow.com/questions/51023312/docker-having-issues-installing-apt-utils
ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Europe/Lisbon
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV GEM_HOME="/home/docker/gems"
ENV PATH="/home/docker/gems/bin:$PATH"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# The install scripts require sudo (no need to clean apt cache, the setup script will install stuff)
RUN apt-get update && apt-get install -y sudo

# Create a user with passwordless sudo
RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo
RUN echo '%docker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER docker
WORKDIR /home/docker/

RUN sudo apt-get update
RUN sudo apt-get install -y \
    tzdata \
    build-essential \
    git \
    gcc \
    g++ \
    make \
    curl \
    zlib1g-dev \
    imagemagick \
    ruby-full

RUN sudo dpkg-reconfigure --frontend noninteractive tzdata

# We need this, otherwise the build blows up with unicode errors
RUN sudo apt-get install -y locales
RUN sudo locale-gen en_US.UTF-8

RUN gem install jekyll bundler

WORKDIR /home/docker/web

# Let's first install all the required gems, but without pulling every file
COPY Gemfile .
RUN bundle install


# Now we copy everything. Rebuilds start here.
COPY --chown=docker . .

CMD [ "make" ]