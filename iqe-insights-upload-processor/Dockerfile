FROM quay.io/cloudservices/iqe-core:latest as builder

USER 0

WORKDIR /iqe_plugin

COPY . .

RUN iqe plugin install --debug . && \
    rm -rf ${HOME}/.cache/pip && \
    chmod -R g+rwX ${IQE_VENV}

FROM quay.io/cloudservices/iqe-core:latest

USER 0
RUN rm -rf "${IQE_VENV}"
COPY --chown=1001:0 --from=builder ${IQE_VENV} ${IQE_VENV}
RUN chmod -R g+rwX "${IQE_VENV}"
USER 1001
