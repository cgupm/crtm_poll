FROM python:3.7 as builder

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY . /tmp/crtm_poll
RUN cd /tmp/crtm_poll; \
    pip install -r requirements_dev.txt; \
    pip install .

FROM python:3.7-alpine

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /tmp/crtm_poll /tmp/crtm_poll

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir /home/user
WORKDIR /home/user
VOLUME /home/user

COPY run_tests.sh /run_tests.sh
RUN chmod 755 /run_tests.sh

ENTRYPOINT ["/opt/venv/bin/crtm_poll"]
