#!/bin/sh
# Issues the first Let's Encrypt certificate. Safe to run on every deploy: it exits early once a real certificate exists.
set -eu

cd "${1:-.}"

env_value() {
    grep -E "^$1=" .env | tail -n 1 | cut -d= -f2- | tr -d '"\r'
}

DOMAIN=$(env_value DOMAIN)
EMAIL=$(env_value LETSENCRYPT_EMAIL || true)
STAGING=$(env_value LETSENCRYPT_STAGING || true)

if [ -z "$DOMAIN" ]; then
    echo "DOMAIN is not set in .env" >&2
    exit 1
fi

mkdir -p certbot/conf certbot/www

if [ -f "certbot/conf/renewal/$DOMAIN.conf" ]; then
    echo "Certificate for $DOMAIN already exists"
    exit 0
fi

certbot_sh() {
    docker compose run -T --rm --no-deps --entrypoint /bin/sh certbot -c "$1"
}

make_placeholder() {
    certbot_sh "mkdir -p /etc/letsencrypt/live/$DOMAIN && openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
        -subj /CN=localhost >/dev/null 2>&1"
}

echo "Creating a temporary certificate so nginx can start"
make_placeholder
docker compose up -d nginx

echo "Requesting a Let's Encrypt certificate for $DOMAIN"
certbot_sh "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf"

args="certonly --webroot -w /var/www/certbot -d $DOMAIN --agree-tos --no-eff-email --non-interactive"
if [ -n "$EMAIL" ]; then
    args="$args --email $EMAIL"
else
    args="$args --register-unsafely-without-email"
fi
if [ "$STAGING" = "1" ]; then
    args="$args --staging"
fi

if ! docker compose run -T --rm --no-deps --entrypoint certbot certbot $args; then
    echo "Certificate request failed. Keeping the temporary certificate." >&2
    make_placeholder
    docker compose exec -T nginx nginx -s reload
    exit 1
fi

docker compose exec -T nginx nginx -s reload
echo "HTTPS is ready at https://$DOMAIN"
