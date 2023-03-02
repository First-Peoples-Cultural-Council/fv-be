import logging
from django.contrib.auth.models import Group, User
from guardian.shortcuts import assign_perm, remove_perm

# A tuple of tuples containing possible states (used in the admin panel and model allowable values for state)
STATE_CHOICES = (
    ('disabled', 'DISABLED'),
    ('enabled', 'ENABLED'),
    ('new', 'NEW'),
    ('published', 'PUBLISHED'),
    ('republish', 'REPUBLISH'),
)

# A mapping of states to state names
STATE_DISABLED = 'disabled'
STATE_ENABLED = 'enabled'
STATE_NEW = 'new'
STATE_PUBLISHED = 'published'
STATE_REPUBLISH = 'republish'

# A lookup for the allowable transitions (eg: if in STATE_DISABLED we can transition to STATE_ENABLED or STATE_PUBLISHED
ALLOWED_TRANSITIONS = {
    STATE_DISABLED: [STATE_ENABLED, STATE_PUBLISHED],
    STATE_ENABLED: [STATE_DISABLED, STATE_NEW, STATE_PUBLISHED],
    STATE_NEW: [STATE_DISABLED, STATE_ENABLED, STATE_PUBLISHED],
    STATE_PUBLISHED: [STATE_DISABLED, STATE_ENABLED, STATE_NEW, STATE_REPUBLISH],
    STATE_REPUBLISH: [STATE_PUBLISHED]
}

# A Mapping of transition names to states
TRANSITIONS = {
    'disable': STATE_DISABLED,
    'enable': STATE_DISABLED,
    'publish': STATE_PUBLISHED,
    'republish': STATE_REPUBLISH,
    'revert_to_new': STATE_NEW,
    'unpublish': STATE_DISABLED
}

# A mapping of states to transition names
TRANSITION_LOOKUP = {
    STATE_DISABLED: 'disable',
    STATE_ENABLED: 'enable',
    STATE_PUBLISHED: 'publish',
    STATE_REPUBLISH: 'republish',
    STATE_NEW: 'revert_to_new'
}


# Takes an input model and transitions it based on an input state.
def follow_lifecycle_transition(model, transition, old_state, initialization=False):
    # Get the public group
    public_group, created = Group.objects.get_or_create(name='public')

    # If no old state parameter is supplied then set the old state to be the input model's state
    if old_state is None:
        old_state = model.state
    # If the transition is an allowed transition or we are initializing a new model then we perform permissions updates
    if TRANSITIONS[transition] in ALLOWED_TRANSITIONS[old_state] or initialization:
        logging.debug(f"Transitioning {model.title} from {old_state} to {TRANSITIONS[transition]}")

        # Get the main language groups for the model
        main_groups = get_main_groups(model)

        # Get the type of model
        model_type = model._meta.model_name

        # Update permissions depending on the transition
        match transition:
            case 'disable':
                remove_perm(f'view_{model_type}', public_group, model)
                remove_perm(f'view_{model_type}', main_groups['member'], model)
                assign_perm(f'view_{model_type}', main_groups['recorder'], model)
                assign_perm(f'view_{model_type}', main_groups['editor'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

            case 'enable':
                remove_perm(f'view_{model_type}', public_group, model)
                assign_perm(f'view_{model_type}', main_groups['member'], model)
                assign_perm(f'view_{model_type}', main_groups['recorder'], model)
                assign_perm(f'view_{model_type}', main_groups['editor'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

            case 'publish':
                assign_perm(f'view_{model_type}', public_group, model)
                assign_perm(f'view_{model_type}', main_groups['member'], model)
                assign_perm(f'view_{model_type}', main_groups['recorder'], model)
                assign_perm(f'view_{model_type}', main_groups['editor'], model)
                assign_perm(f'view_{model_type}', main_groups['language_admin'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

            case 'republish':
                assign_perm(f'view_{model_type}', main_groups['editor'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

            case 'revert_to_new':
                remove_perm(f'view_{model_type}', public_group, model)
                remove_perm(f'view_{model_type}', main_groups['member'], model)
                assign_perm(f'view_{model_type}', main_groups['recorder'], model)
                assign_perm(f'view_{model_type}', main_groups['editor'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

            case 'unpublish':
                remove_perm(f'view_{model_type}', public_group, model)
                assign_perm(f'view_{model_type}', main_groups['member'], model)
                assign_perm(f'view_{model_type}', main_groups['recorder'], model)
                assign_perm(f'view_{model_type}', main_groups['editor'], model)

                if model_type != 'language':
                    assign_perm(f'add_{model_type}', main_groups['editor'], model)
                    assign_perm(f'change_{model_type}', main_groups['editor'], model)

        return TRANSITIONS[transition]

    else:
        logging.debug(f"Transition {transition} not allowed from state {old_state}.")
        print(f"Transition {transition} not allowed from state {old_state}.")
        return old_state


# A helper function to gather the main permissions groups for a language
def get_main_groups(model):
    if model._meta.model_name == 'language':
        language_title = model.title
    else:
        language_title = model.language.title
    member = Group.objects.get(name=f'{language_title}_member')
    recorder = Group.objects.get(name=f'{language_title}_recorder')
    editor = Group.objects.get(name=f'{language_title}_editor')
    language_admin = Group.objects.get(name=f'{language_title}_language_admin')
    return {
        'member': member,
        'recorder': recorder,
        'editor': editor,
        'language_admin': language_admin
    }
