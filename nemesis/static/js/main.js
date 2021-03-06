var current_user = null;
var lastHash = "";
var hashChangeEventListener = null;
var ev = null;
var clv = null;
var ctv = null;
var rv = null;
var sv = null;
var wv = null;

$(document).ready(function() {
    $.ajaxSetup({
        'cache': false
    });
    if (location.hash.length >= 1) {
        location.hash = "";
    }
    var av = new AuthView($("#login-error"));
    clv = new CollegeListView($("#data-college-list"));
    ctv = new CollegeTableView($("#data-college-table"));
    ev = new EditView($("#data-edit-user"), clv.refresh_all);
    rv = new RegisterView($("#data-register-users"));
    sv = new SelfView($("#logged-in-user"));
    wv = new WorkingView($("#messages"));
    $("#login").submit(function() {
        wv.start("Logging in...");
        current_user = new User($("#username").val());
        current_user.login($("#password").val(), function(user) {
            $("#login").hide();
            $("#login-error").hide();
            sv.show(user.username);
            wv.end("Login succeeded");
            if (user.colleges.length <= 1) {
                window.location = '#my-colleges';
            } else {
                // users with a large number of colleges initially get a summary table
                window.location = '#colleges-overview';
                if (user.colleges.length > 3) {
                    // users with a _lot_ of colleges don't get to see
                    // them all in one go as it's really slow
                    $('#my-colleges-link').hide();
                }
                $('.overview-links').show();
            }
        },
        function(response) {
            var errors = response && response.authentication_errors || ['BACKEND_FAIL'];
            av.display_auth_error(errors);
            wv.hide();
        });
        return false;
    });

    $("#username").focus();

    hashChangeEventListener = setInterval("hashChangeEventHandler()", 50);
});

$(document).on("click", ".add-row", function(){
    rv.add_row(college_name_from_hash());
});

function hashChangeEventHandler() {
    var newHash = location.hash.split('#')[1];

    if(newHash != lastHash) {
        lastHash = newHash;
        handle_hash();
    }
}

function handle_hash() {
    ev.hide();
    rv.hide();
    clv.set_all_inactive();
    ctv.hide();

    if (!current_user || !current_user.is_logged_in) {
        return;
    }

    if (location.hash.substring(1,5) == "edit") {
        var username = location.hash.substring(6,location.hash.length);
        wv.start("Loading user");
        ev.show(username, current_user);
        clv.set_active(username);
    } else if (location.hash.substring(1,4) == "reg") {
        rv.show(college_name_from_hash());
        clv.set_register_active(college_name_from_hash());
    } else if (location.hash.substring(1) == "my-colleges") {
        if (current_user.colleges.length > 0) {
            wv.start("Loading college information");
            current_user.fetch_colleges(function(user) {
                clv.render_colleges(user.colleges, !user.is_student);
                wv.hide();
            });
        }
    } else if (location.hash.substring(1) == "colleges-overview") {
        if (current_user.colleges.length > 0) {
            clv.hide();
            wv.start("Loading college information");
            current_user.fetch_colleges(function(user) {
                ctv.render_colleges(user.colleges);
                wv.hide();
            }, true);
        }
    } else if (location.hash.substring(1,8) == "college") {
        var college_name = location.hash.substring(9);
        var college = Colleges[college_name];
        if (!college) {
            return;
        }
        wv.start("Loading college");
        college.fetch(function(c) {
            clv.render_colleges([c], !current_user.is_student);
            wv.hide();
        });
    }
}

function clear_view() {
    location.hash = '';
}

function college_name_from_hash() {
    return location.hash.substring(5,location.hash.length);
}

function isASCII(str) {
    return /^[\x00-\x7F]*$/.test(str);
}

function isEmail(str) {
    return /^.+@.+\...+$/.test(str);
}
