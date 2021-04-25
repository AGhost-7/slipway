FROM python:3

RUN useradd --uid 1001 --create-home foobar && \
	apt-get update && \
	apt-get install -y tmux sudo

USER foobar

VOLUME /test-volume

COPY ./entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/bin/bash"]
