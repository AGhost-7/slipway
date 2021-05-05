FROM python:3

RUN apt-get update && \
	apt-get install -y tmux sudo nmap strace && \
    adduser --uid 1001 --disabled-password --gecos '' foobar && \
	adduser foobar sudo && \
	echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER foobar

VOLUME /test-volume

COPY ./entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/bin/bash"]
