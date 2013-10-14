var savoryPieInterface = function() {
    var hashes = {};
    var savoryPieGet = function(url) {
        $.ajax(url).complete(function(response) {
            if (response.status === 200) {
            }
        });
    };
    var savoryPiePost = function(url) {

    };
    var savoryPiePut = function(url) {

    };
    var savoryPieDelete = function(url) {

    };

    return {
        get: savoryPieGet,
        post: savoryPiePost,
        put: savoryPiePut,
        delete: savoryPieDelete
    };
};

