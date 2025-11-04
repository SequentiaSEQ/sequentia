FROM ubuntu:24.04 as builder

RUN set -ex \
	&& apt-get update \
	&& apt-get install -qq --no-install-recommends ca-certificates wget \
	&& cd /tmp \
	&& wget -qO sequentia.tar.gz "https://github.com/SequentiaSEQ/sequentia/releases/download/testnet-v0.3/sequentia-testnet-linux.tar.gz" \
	&& mkdir bin \
	&& tar -xzvf sequentia.tar.gz -C /tmp/bin --strip-components=2 "sequentia-testnet-linux/bin/elements-cli" "sequentia-testnet-linux/bin/elementsd"

FROM ubuntu:24.04

COPY --from=builder "/tmp/bin" /usr/local/bin

# Expose volume containing all `elementsd` data
VOLUME $DIR/.elements/


ENTRYPOINT [ "elementsd" ]