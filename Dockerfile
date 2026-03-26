# ── Base image ────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim

LABEL maintainer="your-email@example.com"
LABEL description="NDPI to BIDS converter"
LABEL version="alpha.0.1.0"

# ── System dependencies ────────────────────────────────────────────────────────
# openjdk-17-jre: required by bfconvert (Bio-Formats)
# libtiff5 / libopenjp2-7: tifffile native support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    openjdk-17-jre-headless \
    libtiff6 \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

# ── Install kiki ───────────────────────────────────────────────────────────────
# kiki: https://github.com/kiki-kanri/kiki  (lightweight env manager)
RUN curl -fsSL https://raw.githubusercontent.com/kiki-kanri/kiki/main/install.sh \
    | bash -s -- --prefix /opt/kiki \
    && ln -s /opt/kiki/bin/kiki /usr/local/bin/kiki

# ── Install bfconvert (Bio-Formats command-line tools) ────────────────────────
# https://www.openmicroscopy.org/bio-formats/downloads/
ARG BF_VERSION=7.3.1
RUN curl -fsSL \
    "https://downloads.openmicroscopy.org/bio-formats/${BF_VERSION}/artifacts/bftools.zip" \
    -o /tmp/bftools.zip \
    && unzip /tmp/bftools.zip -d /opt/ \
    && rm /tmp/bftools.zip \
    && chmod +x /opt/bftools/bfconvert \
    && ln -s /opt/bftools/bfconvert /usr/local/bin/bfconvert

# ── Set working directory ──────────────────────────────────────────────────────
WORKDIR /app

# ── Copy environment spec and install Python dependencies ─────────────────────
COPY environment.yml .
RUN kiki env create -f environment.yml

# ── Copy source code and templates ────────────────────────────────────────────
COPY ndpi2bids/ ./ndpi2bids/
COPY templates/  ./templates/

# ── Default command ────────────────────────────────────────────────────────────
ENTRYPOINT ["kiki", "run", "python", "ndpi2bids/ndpi2bids.py"]
CMD ["--help"]