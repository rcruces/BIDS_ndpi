# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Thrown away after build — CVEs here never reach the final image
FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install kiki
RUN curl -fsSL https://raw.githubusercontent.com/kiki-kanri/kiki/main/install.sh \
    | bash -s -- --prefix /opt/kiki

# Download bfconvert (Bio-Formats command-line tools)
# https://www.openmicroscopy.org/bio-formats/downloads/
ARG BF_VERSION=7.3.1
RUN curl -fsSL \
    "https://downloads.openmicroscopy.org/bio-formats/${BF_VERSION}/artifacts/bftools.zip" \
    -o /tmp/bftools.zip \
    && unzip /tmp/bftools.zip -d /opt/ \
    && rm /tmp/bftools.zip \
    && chmod +x /opt/bftools/bfconvert

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
# Only this stage is shipped — Python is pre-installed, smaller attack surface
FROM python:3.11-slim-bookworm AS runtime

LABEL maintainer="raul.rodriguezcruces@mcgill.ca"
LABEL description="NDPI to BIDS converter"
LABEL version="alpha.0.1.0"

# openjdk-17-jre: required by bfconvert
# libtiff6 / libopenjp2-7: tifffile native support
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    libtiff6 \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

# Copy kiki and bftools from builder — curl, unzip, apt cache are left behind
COPY --from=builder /opt/kiki    /opt/kiki
COPY --from=builder /opt/bftools /opt/bftools

RUN ln -s /opt/kiki/bin/kiki      /usr/local/bin/kiki \
    && ln -s /opt/bftools/bfconvert /usr/local/bin/bfconvert

# ── Set working directory ──────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
COPY environment.yml .
RUN kiki env create -f environment.yml

# ── Copy source code ──────────────────────────────────────────────────────────
# templates/ now lives inside ndpi2bids/ — no separate COPY needed
COPY ndpi2bids/ ./ndpi2bids/

# ── Default command ────────────────────────────────────────────────────────────
ENTRYPOINT ["kiki", "run", "python", "ndpi2bids/ndpi2bids.py"]
CMD ["--help"]