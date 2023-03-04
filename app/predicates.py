import rules


@rules.predicate
def is_super_admin(user):
    return user.is_superuser

@rules.predicate
def is_published(user, language):
    return language.state == 'published'


@rules.predicate
def is_enabled(user, language):
    return language.state == 'enabled'


@rules.predicate
def is_disabled(user, language):
    return language.state == 'disabled'


@rules.predicate
def is_new(user, language):
    return language.state == 'new'


@rules.predicate
def is_republish(user, language):
    return language.state == 'republish'


@rules.predicate
def is_member(user, model):
    if model._meta.model_name == 'language':
        language_title = model.title
    else:
        language_title = model.language.title
    return user.groups.filter(name=f'{language_title}_member').exists()


@rules.predicate
def is_recorder(user, model):
    if model._meta.model_name == 'language':
        language_title = model.title
    else:
        language_title = model.language.title
    return user.groups.filter(name=f'{language_title}_recorder').exists()


@rules.predicate
def is_editor(user, model):
    if model._meta.model_name == 'language':
        language_title = model.title
    else:
        language_title = model.language.title
    return user.groups.filter(name=f'{language_title}_editor').exists()


@rules.predicate
def is_language_admin(user, model):
    if model._meta.model_name == 'language':
        language_title = model.title
    else:
        language_title = model.language.title
    return user.groups.filter(name=f'{language_title}_language_admin').exists()


@rules.predicate
def is_language_published(user, model):
    if model._meta.model_name == 'language':
        language_state = model.state
    else:
        language_state = model.language.state
    return language_state == 'published'
