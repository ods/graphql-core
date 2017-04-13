from promise import Promise
from promise.dataloader import DataLoader

from graphql import GraphQLObjectType, GraphQLField, GraphQLID, GraphQLArgument, GraphQLNonNull, GraphQLSchema, parse, execute


def test_batches_correctly():

    Business = GraphQLObjectType('Business', lambda: {
        'id': GraphQLField(GraphQLID, resolver=lambda root, args, context, info: root),
    })

    Query = GraphQLObjectType('Query', lambda: {
        'getBusiness': GraphQLField(Business,
            args={
                'id': GraphQLArgument(GraphQLNonNull(GraphQLID)),
            },
            resolver=lambda root, args, context, info: context.business_data_loader.load(args.get('id'))
        ),
    })

    schema = GraphQLSchema(query=Query)


    doc = '''
{
    business1: getBusiness(id: "1") {
        id
    }
    business2: getBusiness(id: "2") {
        id
    }
}
    '''
    doc_ast = parse(doc)


    load_calls = []
    
    class BusinessDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            load_calls.append(keys)
            return Promise.resolve(keys)

    class Context(object):
        business_data_loader = BusinessDataLoader()


    result = execute(schema, doc_ast, None, context_value=Context())
    assert not result.errors
    assert result.data == {
        'business1': {
            'id': '1'
        },
        'business2': {
            'id': '2'
        },
    }
    assert load_calls == [['1','2']]


def test_batches_multiple_together():

    Location = GraphQLObjectType('Location', lambda: {
        'id': GraphQLField(GraphQLID, resolver=lambda root, args, context, info: root),
    })

    Business = GraphQLObjectType('Business', lambda: {
        'id': GraphQLField(GraphQLID, resolver=lambda root, args, context, info: root),
        'location': GraphQLField(Location,
            resolver=lambda root, args, context, info: context.location_data_loader.load('location-{}'.format(root))
        ),
    })

    Query = GraphQLObjectType('Query', lambda: {
        'getBusiness': GraphQLField(Business,
            args={
                'id': GraphQLArgument(GraphQLNonNull(GraphQLID)),
            },
            resolver=lambda root, args, context, info: context.business_data_loader.load(args.get('id'))
        ),
    })

    schema = GraphQLSchema(query=Query)


    doc = '''
{
    business1: getBusiness(id: "1") {
        id
        location {
            id
        }
    }
    business2: getBusiness(id: "2") {
        id
        location {
            id
        }
    }
}
    '''
    doc_ast = parse(doc)


    business_load_calls = []
    
    class BusinessDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            business_load_calls.append(keys)
            return Promise.resolve(keys)

    location_load_calls = []
    
    class LocationDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            location_load_calls.append(keys)
            return Promise.resolve(keys)

    class Context(object):
        business_data_loader = BusinessDataLoader()
        location_data_loader = LocationDataLoader()


    result = execute(schema, doc_ast, None, context_value=Context())
    assert not result.errors
    assert result.data == {
        'business1': {
            'id': '1',
            'location': {
                'id': 'location-1'
            }
        },
        'business2': {
            'id': '2',
            'location': {
                'id': 'location-2'
            }
        },
    }
    assert business_load_calls == [['1','2']]
    assert location_load_calls == [['location-1','location-2']]
