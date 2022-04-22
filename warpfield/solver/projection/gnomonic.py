#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' gnomonic projection '''

import jax.numpy as jnp
from jax import vmap


def degree_to_radian(theta):
    ''' convert degree to radian '''
    return theta * jnp.pi / 180.


def rotation_matrix(theta):
    ''' calculate rotation matrix R '''
    rot = [jnp.cos(theta), -jnp.sin(theta), jnp.sin(theta), jnp.cos(theta)]
    return jnp.array(rot).reshape([2, 2])


def gnomonic_x(tel_ra, tel_dec, ra, dec):
    ''' calculate internal spherical coordinate x '''
    return jnp.sin(tel_dec) * jnp.cos(dec) * jnp.cos(ra - tel_ra) \
        - jnp.cos(tel_dec) * jnp.sin(dec)


def gnomonic_y(tel_ra, tel_dec, ra, dec):
    ''' calculate internal spherical coordinate y '''
    return jnp.cos(dec) * jnp.sin(ra - tel_ra)


def gnomonic_z(tel_ra, tel_dec, ra, dec):
    ''' calculate internal spherical coordinate z '''
    return jnp.cos(tel_dec) * jnp.cos(dec) * jnp.cos(ra - tel_ra) \
        + jnp.sin(tel_dec) * jnp.sin(dec)


def gnomonic_conversion(tel_ra, tel_dec, ra, dec):
    ''' gnomonic projection '''
    x = gnomonic_x(tel_ra, tel_dec, ra, dec)
    y = gnomonic_y(tel_ra, tel_dec, ra, dec)
    z = gnomonic_z(tel_ra, tel_dec, ra, dec)
    radius = 180.0 / jnp.pi * jnp.sqrt(1 / z**2 - 1)
    phi = jnp.arctan2(x, -y)
    return radius * jnp.cos(phi), -radius * jnp.sin(phi)


def gnomonic(tel_ra, tel_dec, tel_pa, ra, dec, scale):
    ''' gnomonic projection of the spherical coordinates.

    Arguments:
      tel_ra: right ascension of the telescope center.
      tel_dec: declinatoin of the telescope center.
      tel_pa: position angle of the telescope.
      ra: right ascension of the target.
      dec: declination of the target.
      scale: physical scale of the focal plane (mm/deg).

    Returns:
      converted coordinates on the focal plane
    '''
    tel_ra = degree_to_radian(tel_ra)
    tel_dec = degree_to_radian(tel_dec)
    tel_pa = degree_to_radian(tel_pa)
    ra = degree_to_radian(ra)
    dec = degree_to_radian(dec)
    X, Y = gnomonic_conversion(tel_ra, tel_dec, ra, dec)
    return (rotation_matrix(tel_pa) @ jnp.stack([X, Y])).T * scale


projection = vmap(gnomonic, (0, 0, 0, 0, 0, 0), 0)