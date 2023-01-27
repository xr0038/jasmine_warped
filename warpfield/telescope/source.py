#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' Handling astronomical sources '''

from astropy.coordinates import SkyCoord, Angle, Distance
from astropy.time import Time
from astroquery.gaia import Gaia
import astropy.units as u
import matplotlib.pyplot as plt

from .util import get_projection, estimate_frame_from_ctype

__debug_mode__ = False


def gaia_query_builder(pointing, radius, snr_limit, catalog='gaiaedr3'):
    ''' Construct a query string

    Arguments:
      pointing: A center of the search circle.
      radius: A serach radius.
      snr_limit: A lower limit of `parallax_over_error`.
      catalog: The name of catalog (default: `gaiaedr3`)

    Returns:
      A SQL query string.
    '''
    return f'''
    SELECT
        source_id,
        ra,
        dec,
        phot_g_mean_mag,
        pmra,
        pmdec,
        parallax,
        ref_epoch
    FROM
        {catalog}.gaia_source
    WHERE
        1=CONTAINS(
          POINT('ICRS', {pointing.icrs.ra.deg}, {pointing.icrs.dec.deg}),
          CIRCLE('ICRS', ra, dec, {radius.deg}))
    AND
        parallax_over_error > {snr_limit}
    '''


def retrieve_gaia_sources(pointing, radius, snr_limit=10.0, row_limit=-1):
    ''' Retrive sources around (lon, lat) from Gaia EDR3 catalog

    Arguments:
      pointing (SkyCoord):
          Celestial coordinates of the search center.
      radius (float or Angle):
          A search radius in degree.
      snr_limit (float, optional):
          A lower limit of `parallax_over_error`.
      row_limit (int, optional):
          The maximum number of records.
          `-1` means no limit in the number of records.

    Return:
      A list of neighbour souces (SkyCoord).
    '''

    # Get an acceess to the Gaia TAP+.
    #   - Set the target table to Gaia DR3.
    #   - Remove the limit of the query number.
    Gaia.MAIN_GAIA_TABLE = 'gaiadr3.gaia_source'
    Gaia.ROW_LIMIT = row_limit

    if not isinstance(radius, Angle):
        radius = Angle(radius, unit=u.degree)

    pointing = pointing.transform_to('icrs')
    query = gaia_query_builder(pointing, radius, snr_limit)

    res = Gaia.launch_job_async(query)

    if __debug_mode__ is True:
        print(res)

    record = res.get_results()
    epoch = Time(record['ref_epoch'].data, format='decimalyear')

    obj = SkyCoord(ra=record['ra'],
                   dec=record['dec'],
                   pm_ra_cosdec=record['pmra'],
                   pm_dec=record['pmdec'],
                   distance=Distance(parallax=record['parallax'].data * u.mas),
                   obstime=epoch)
    return obj


def get_subplot(pointing, key=111, figsize=(8, 8)):
    ''' Generate an axis instance for a poiting

    Arguments:
      pointing (SkyCoord):
          The directin of the telescope pointing.
      frame (string):
          Set to override the projection of `pointing`.
    '''
    proj = get_projection(pointing)

    fig = plt.figure(figsize=figsize)
    axis = fig.add_subplot(key, projection=proj)

    return fig, axis


def display_sources(axis, sources, **options):
    ''' Display sources around the specified coordinates

    Arguments:
      axis (Axes):
          Matplotlib Axes instance.
      pointing (SkyCoord):
          The direction of the telescope pointing.
      sources (SkyCoord):
          The list of sources.
    '''
    ctype = axis.wcs.wcs.ctype
    frame = estimate_frame_from_ctype(ctype)

    if frame == 'galactic':
        get_lon = lambda x: getattr(x, 'galactic').l
        get_lat = lambda x: getattr(x, 'galactic').b
        xlabel = 'Galactic Longitude'
        ylabel = 'Galactic Latitude'
    else:
        get_lon = lambda x: getattr(x, 'icrs').ra
        get_lat = lambda x: getattr(x, 'icrs').dec
        xlabel = 'Right Ascension'
        ylabel = 'Declination'

    title = options.pop('title', None)
    marker = options.pop('marker', 'x')
    axis.set_aspect(1.0)
    axis.set_position([0.13, 0.10, 0.85, 0.85])
    axis.scatter(get_lon(sources),
                 get_lat(sources),
                 transform=axis.get_transform(frame),
                 marker=marker,
                 label=title,
                 **options)
    axis.grid()
    if title is not None:
        axis.legend(bbox_to_anchor=[1, 1], loc='lower right', frameon=False)
    axis.set_xlabel(xlabel, fontsize=14)
    axis.set_ylabel(ylabel, fontsize=14)


def display_gaia_sources(pointing, radius=0.1):
    ''' Display Gaia EDR3 sources around the coordinate

    Arguments:
      pointing (SkyCoord):
          Celestial coordinate of the search center.
      radius (float or Angle):
          A search radius in degree.

    Returns:
      A tuble of (figure, axis).
    '''
    src = retrieve_gaia_sources(pointing, radius)
    return display_sources(pointing, src)
