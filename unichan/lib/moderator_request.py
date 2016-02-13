# Helper methods for managing the moderator attached to the session

from flask import session

from unichan import g
from unichan.lib import ArgumentError


def get_authed():
    return 'mod_auth_id' in session


def get_authed_moderator():
    if not get_authed():
        raise ArgumentError('Not authed')
    mod = g.moderator_service.find_moderator_id(session['mod_auth_id'])
    if mod is None:
        raise ArgumentError('Mod not found')
    return mod


def request_has_role(role):
    moderator = get_authed_moderator()
    return moderator is not None and g.moderator_service.has_role(moderator, role)


def set_mod_authed(moderator):
    session['mod_auth_id'] = moderator.id


def unset_mod_authed():
    del session['mod_auth_id']
