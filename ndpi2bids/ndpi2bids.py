#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on March 12, 2026
@author: rcruces

BAsed on the BIDS Microscopy Extension proposal and inspired by the MICA lab's work on precision neuroimaging and connectomics. 
This tool is designed to convert Hamamatsu NDPI files into a BIDS-compliant format, 
facilitating standardized data sharing and analysis in the neuroscience community.

Bourget, M. H., Kamentsky, L., Ghosh, S. S., Mazzamuto, G., Lazari, A., Markiewicz, C. J., ... & Cohen-Adad, J. (2022). 
Microscopy-BIDS: an extension to the brain imaging data structure for microscopy data. Frontiers in Neuroscience, 16, 871228.
https://doi.org/10.3389/fnins.2022.871228
"""

import os
import re
import json
import shutil
import argparse
import subprocess
import tifffile
import logging
import xml.etree.ElementTree as ET

# --- Class Definitions ---

class BIDS_micr_name:
    """Generates BIDS-compliant paths and filenames for microscopy data."""
    def __init__(self, **kwargs):
        self.entities = ["sub", "ses", "sample", "acq", "stain", "run", "chunk"]
        self.values = kwargs

    def build(self):
        sub_val = self.values.get("sub")
        ses_val = self.values.get("ses")
        
        path_segments = [f"sub-{sub_val}"]
        if ses_val:
            path_segments.append(f"ses-{ses_val}")
        path_segments.append("micr")
        
        directory_prefix = "/".join(path_segments)

        filename_parts = []
        for entity in self.entities:
            if entity in self.values and self.values[entity]:
                filename_parts.append(f"{entity}-{self.values[entity]}")

        suffix = self.values.get("suffix", "BF")
        filename = "_".join(filename_parts) + f"_{suffix}"
        return f"{directory_prefix}/{filename}"

class BIDS_micr_metadata:
    """Extracts and stores BIDS metadata for microscopy."""
    def __init__(self, ndpi_path, template_path=None, **kwargs):
        self.path = ndpi_path

        # Keys that will be filled from NDPI file headers
        self.metadata = {
            "Manufacturer": None,
            "ManufacturersModelName": None,
            "PixelSize": None,
            "PixelSizeUnits": None,
            "Magnification": None,
            "ImageAcquisitionProtocol": None,
            "ScanTimeSeconds": None,
            "FocusTimeSeconds": None,
            "Software": None,
            "DateAcquired": None,
            "Compression": None,
            "BitsPerPixel": None,
        }

        # Load remaining keys from template JSON
        if template_path is None:
            template_path = os.path.join(
                os.path.dirname(__file__), "templates", "stain-AT8_BF.json"
            )
        if os.path.isfile(template_path):
            with open(template_path, "r") as f:
                template_data = json.load(f)
            # Template values fill in keys not already defined above
            for key, value in template_data.items():
                if key not in self.metadata:
                    self.metadata[key] = value
                elif self.metadata[key] is None and value is not None:
                    self.metadata[key] = value

        # Override any metadata value with user-supplied kwargs
        for key, value in kwargs.items():
            self.metadata[key] = value

    def fill_from_ndpi(self):
        """Extract pre-selected keys from NDPI file headers.

        Populates: Manufacturer, ManufacturersModelName, PixelSize,
        NumericalAperture, PixelSizeUnits, Magnification,
        ImageAcquisitionProtocol, ScanTimeSeconds, FocusTimeSeconds,
        Software, DateAcquired, Compression, BitsPerPixel
        """
        with tifffile.TiffFile(self.path) as tif:
            page = tif.pages[0]

            # ------ helper: flat dict from all NDPI custom tags ------
            ndpi_info = getattr(tif, 'ndpi_tags', {})

            # ------ helper: ImageDescription text ------
            desc_tag = page.tags.get('ImageDescription')
            desc_str = str(desc_tag.value) if desc_tag else ""

            # ---- Manufacturer & Model ----
            make_tag = page.tags.get('Make')
            if make_tag:
                self.metadata["Manufacturer"] = str(make_tag.value).strip()
            model_tag = page.tags.get('Model')
            if model_tag:
                self.metadata["ManufacturersModelName"] = str(model_tag.value).strip()

            # ---- Software ----
            sw_tag = page.tags.get('Software')
            if sw_tag:
                self.metadata["Software"] = str(sw_tag.value).strip()
            elif ndpi_info.get('Software'):
                self.metadata["Software"] = ndpi_info['Software']

            # ---- PixelSize (µm) from OME-XML ----
            try:
                if tif.ome_metadata:
                    root = ET.fromstring(tif.ome_metadata.strip())
                    pixels = root.find(".//{*}Pixels")
                    if pixels is not None:
                        self.metadata["PixelSize"] = [
                            round(float(pixels.get('PhysicalSizeX', 0)), 4),
                            round(float(pixels.get('PhysicalSizeY', 0)), 4),
                        ]
            except Exception:
                pass

            # ---- PixelSize fallback: NDPI Distance tag ----
            if not self.metadata["PixelSize"] and ndpi_info.get('Distance'):
                psize = round(float(ndpi_info['Distance']) / 1000.0, 4)
                self.metadata["PixelSize"] = [psize, psize]

            # ---- PixelSize fallback: TIFF resolution tags ----
            if not self.metadata["PixelSize"]:
                x_res = page.tags.get('XResolution')
                unit = page.tags.get('ResolutionUnit')
                if x_res and unit:
                    res_val = x_res.value[0] / x_res.value[1]
                    if unit.value == 3:
                        psize = 10000.0 / res_val
                    elif unit.value == 2:
                        psize = 25400.0 / res_val
                    else:
                        psize = None
                    if psize is not None:
                        self.metadata["PixelSize"] = [round(psize, 4), round(psize, 4)]

            # BIDS requires µm
            self.metadata["PixelSizeUnits"] = "um"

            # ---- NumericalAperture ----
            try:
                if tif.ome_metadata:
                    root = ET.fromstring(tif.ome_metadata.strip())
                    obj = root.find(".//{*}Objective")
                    if obj is not None:
                        na = obj.get('LensNA')
                        if na:
                            self.metadata["NumericalAperture"] = float(na)
            except Exception:
                pass

            if not self.metadata.get("NumericalAperture") and ndpi_info:
                self.metadata["NumericalAperture"] = (
                    ndpi_info.get('NA') or ndpi_info.get('NumericalAperture')
                )

            if not self.metadata.get("NumericalAperture") and desc_str:
                na_match = re.search(
                    r'(?:NA|N\.A\.|Numerical\s?Aperture)[:\s=]+([0-9\.]+)',
                    desc_str, re.IGNORECASE,
                )
                if na_match:
                    self.metadata["NumericalAperture"] = float(na_match.group(1))

            # ---- Magnification ----
            mag = ndpi_info.get('Magnification')
            if mag is not None:
                self.metadata["Magnification"] = float(mag)
            elif desc_str:
                mag_match = re.search(r'(\d+)[xX]\b', desc_str)
                if mag_match:
                    self.metadata["Magnification"] = float(mag_match.group(1))

            # ---- Compression ----
            self.metadata["Compression"] = str(page.compression)

            # ---- BitsPerPixel ----
            self.metadata["BitsPerPixel"] = int(page.bitspersample * page.samplesperpixel)

            # ---- DateAcquired ----
            dt_tag = page.tags.get('DateTime')
            if dt_tag:
                self.metadata["DateAcquired"] = str(dt_tag.value).strip()
            elif ndpi_info.get('DateTime'):
                self.metadata["DateAcquired"] = ndpi_info['DateTime']

            # ---- ScanTimeSeconds / FocusTimeSeconds ----
            if ndpi_info.get('ScanTime'):
                self.metadata["ScanTimeSeconds"] = float(ndpi_info['ScanTime'])
            if ndpi_info.get('FocusTime'):
                self.metadata["FocusTimeSeconds"] = float(ndpi_info['FocusTime'])

    def save_json(self, output_path):
        """Writes the dictionary to a BIDS-compliant JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.metadata, f, indent=4)

# --- Execution Script ---

def main():
    parser = argparse.ArgumentParser(description="Convert NDPI files to BIDS Microscopy format (MNI Neuropathology).")
    
    # Mandatory BIDS arguments
    parser.add_argument("--ndpi_path", required=True, help="Path to raw Hamamatsu .ndpi file")
    parser.add_argument("--bids", required=True, help="Path to the root of the BIDS dataset")
    parser.add_argument("--sub", required=True, help="Subject ID (e.g., PX067)")
    parser.add_argument("--stain", required=True, help="Stain entity (e.g., AT8)")
    parser.add_argument("--suffix", required=True, help="BIDS suffix (e.g., BF)")

    # Optional BIDS entities
    parser.add_argument("--ses", help="Session ID")
    parser.add_argument("--sample", help="Sample ID (e.g., NP24709)")
    parser.add_argument("--acq", help="Acquisition label")
    parser.add_argument("--run", help="Run index")
    parser.add_argument("--chunk", help="Chunk label (e.g., A3)")
    parser.add_argument("--template", help="JSON template for metadata (optional, overrides defaults)")
    parser.add_argument(
        "--meta", nargs="*", metavar="KEY=VALUE",
        help='Override template metadata values, e.g. --meta BodyPartDetails=Hippocampus SampleFixation="formalin 20%%"'
    )

    # Operational flags
    parser.add_argument("--convert", action="store_true", help="Convert NDPI to OME-TIFF via bfconvert")
    parser.add_argument("--dry_run", action="store_true", help="Perform a dry run without actually converting, printing intended actions instead")
    parser.add_argument("--force", action="store_true", help="Overwrite existing BIDS files and sidecars")

    args = parser.parse_args()

    # --- Parse --meta key=value pairs into a dict ---
    meta_overrides = {}
    if args.meta:
        for item in args.meta:
            if "=" not in item:
                parser.error(f"Invalid --meta format '{item}'. Expected KEY=VALUE.")
            key, value = item.split("=", 1)
            meta_overrides[key] = value

    # --- 1. Setup Naming and Directory Logic ---
    entities = {k: v for k, v in vars(args).items() if v is not None}
    bids_namer = BIDS_micr_name(**entities)
    bids_rel_path = bids_namer.build()
    full_bids_base = os.path.join(args.bids, bids_rel_path)

    target_ndpi = f"{full_bids_base}.ndpi"
    target_json = f"{full_bids_base}.json"
    target_ome  = f"{full_bids_base}.ome.tif"

    # --- Dry-run mode: print intended actions and exit ---
    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"  Source NDPI  : {args.ndpi_path}")
        print(f"  BIDS root    : {args.bids}")
        print(f"  Target NDPI  : {target_ndpi}")
        print(f"  Target JSON  : {target_json}")
        if args.convert:
            print(f"  Target OME   : {target_ome}")
        if args.force:
            print("  Mode         : FORCE (overwrite existing files)")
        if args.template:
            print(f"  Template     : {args.template}")
        if meta_overrides:
            print(f"  Meta overrides: {meta_overrides}")
        exists_ndpi = os.path.exists(target_ndpi)
        exists_json = os.path.exists(target_json)
        print(f"  NDPI exists  : {exists_ndpi}")
        print(f"  JSON exists  : {exists_json}")
        if exists_ndpi and not args.force:
            print("  Action       : SKIP (target exists, use --force to overwrite)")
        else:
            print(f"  Action       : {'OVERWRITE' if exists_ndpi else 'COPY'} NDPI + write JSON sidecar")
        print("=== END DRY RUN ===")
        return

    # Define log location at the same level as /micr
    subject_session_root = os.path.dirname(os.path.dirname(full_bids_base))
    log_dir = os.path.join(subject_session_root, "log")
    os.makedirs(log_dir, exist_ok=True)

    # --- 2. Setup Logging ---
    log_name_parts = [f"sub-{args.sub}"]
    if args.ses: log_name_parts.append(f"ses-{args.ses}")
    log_name_parts.append("bids-micr.log")

    log_file = os.path.join(log_dir, "_".join(log_name_parts))

    # Configure logging to write to the new subject-specific file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )

    logging.info(f"Processing started for: {args.ndpi_path}")

    try:
        # Step 3: Directories and Copy
        os.makedirs(os.path.dirname(full_bids_base), exist_ok=True)

        if os.path.exists(target_ndpi) and not args.force:
            logging.info(f"SKIPPED: {target_ndpi} exists. Use --force to overwrite.")
            return

        status_prefix = "OVERWRITE" if os.path.exists(target_ndpi) else "NEW"
        logging.info(f"{status_prefix}: Copying NDPI to {target_ndpi}")
        shutil.copy2(args.ndpi_path, target_ndpi)

        # Step 4: Metadata
        logging.info("Metadata: Extracting from headers...")
        meta = BIDS_micr_metadata(
            target_ndpi,
            template_path=args.template,
            **meta_overrides,
        )
        meta.fill_from_ndpi()
        meta.save_json(target_json)
        logging.info("Metadata: JSON sidecar saved.")

        # Step 5: Optional Conversion
        if args.convert:
            if os.path.exists(target_ome) and not args.force:
                logging.info("Conversion: OME-TIFF exists, skipping.")
            else:
                logging.info("Conversion: Starting bfconvert...")
                result = subprocess.run(
                    ['bfconvert', '-bigtiff', '-compression', 'LZW', target_ndpi, target_ome],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    logging.info(f"Conversion: Success -> {target_ome}")
                else:
                    logging.error(f"Conversion: Failed -> {result.stderr}")

        logging.info(f"STATUS: SUCCESS for sub-{args.sub}")

    except Exception as e:
        logging.error(f"STATUS: FAILED for sub-{args.sub} - {str(e)}")

if __name__ == "__main__":
    main()