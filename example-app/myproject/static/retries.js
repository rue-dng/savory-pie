var savoryPieInterface = function() {
    var hashes = {};
    var savoryPieGet = function(url, happy, sad) {
        $.ajax(url).complete(function(response) {
            if (response.status === 200) {
                happy(response);
            } else {
                sad(response);
            }
        });
    };
    var savoryPiePost = function(url) {

    };
    var savoryPiePut = function(url, happy, sad) {
        $.ajax(url).complete(function(response) {
            if (response.status === 200) {
                happy(response);
            } else if (response.status === 409) {
                // do the retry stuff
            } else if (response.status === 412) {
                // do the merge stuff
            } else {
                sad(response);
            }
        });
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

