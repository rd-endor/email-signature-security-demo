# CVE-2026-109618 and CVE-2026-109619 are matched by Endor to the
# Debian source package php8.4, fixed in 8.4.27-1~deb13u1.
# The official php image compiles PHP from source and is recorded as
# sbom://php, which does not match that package.
# The trixie suite, without trixie-security, still publishes a php8.4
# below that fix.
FROM debian:trixie

RUN rm -rf /etc/apt/sources.list.d \
    && printf 'deb http://deb.debian.org/debian trixie main\n' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends php8.4-cli \
    && rm -rf /var/lib/apt/lists/*

COPY public/ /var/www/html/

EXPOSE 80
CMD ["php", "-S", "0.0.0.0:80", "-t", "/var/www/html"]
