"""Explicit source-validation exception; default opposite-embryo guard retained."""
MOVIES = frozenset(['44b6_53f95252','44b6_551a5dba','44b6_aaf8b0ea','44b6_c771cb04',
                    '44b6_c8e2a523','44b6_d754aa59','44b6_d78e09d9','44b6_e31261b4'])


def validate_scope(bundle, movies):
    names=list(movies)
    assert names and len(names)==len(set(names))
    source=bundle['source_embryo']
    if bundle.get('evaluation_mode')=='EXP221_SOURCE_VALIDATION_FIXED8':
        assert source=='44b6' and set(names)==MOVIES
        assert set(bundle['source_validation_movies'])==MOVIES
        assert not MOVIES.intersection(bundle['source_train_movies'])
    else:
        assert all(not n.startswith(source+'_') for n in names), 'Target is source embryo'


def test():
    b={'source_embryo':'44b6'}
    validate_scope(b,['6bba_opposite'])
    s={**b,'evaluation_mode':'EXP221_SOURCE_VALIDATION_FIXED8','source_validation_movies':sorted(MOVIES),'source_train_movies':['44b6_train']}
    validate_scope(s,sorted(MOVIES))
    for bundle,movies in [(b,sorted(MOVIES)),(s,['6bba_opposite']),(s,sorted(MOVIES)[:-1]),
                          (s,[*sorted(MOVIES),'44b6_train']),({**s,'source_train_movies':sorted(MOVIES)},sorted(MOVIES))]:
        try: validate_scope(bundle,movies)
        except AssertionError: pass
        else: raise AssertionError('Scope guard accepted forbidden cohort')
    print('PASS_SOURCE8_ALLOWLIST_AND_DEFAULT_TARGET_GUARD')


if __name__=='__main__':test()
