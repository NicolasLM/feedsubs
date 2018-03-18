document.addEventListener('DOMContentLoaded', function () {

    // Get all "navbar-burger" elements
    var $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);

    // Check if there are any navbar burgers
    if ($navbarBurgers.length > 0) {

        // Add a click event on each of them
        $navbarBurgers.forEach(function ($el) {
            $el.addEventListener('click', function () {

                // Get the target from the "data-target" attribute
                var target = $el.dataset.target;
                var $target = document.getElementById(target);

                // Toggle the class on both the "navbar-burger" and the "navbar-menu"
                $el.classList.toggle('is-active');
                $target.classList.toggle('is-active');

            });
        });
    }

});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


function star()
{
    var current = $(this);
    var type = current.data('type');
    var pk = current.data('id');
    var action = current.data('action');
    var url;

    if (pk === "") {
        url = "/" + type + "/" + action;
    } else {
        url = "/" + type + "/" + pk + "/" + action;
    }

    $.ajax({
        url: url,
        type: 'POST',
        statusCode: {
            204: function () {
                if (action === "star") {
                    current.addClass("is-warning is-selected");
                    current.data("action", "unstar");
                } else if (action === "unstar") {
                    current.removeClass("is-warning is-selected");
                    current.data("action", "star");
                } else if (action === "read") {
                    current.addClass("is-success is-selected");
                    current.data("action", "unread");
                } else if (action === "unread") {
                    current.removeClass("is-success is-selected");
                    current.data("action", "read");
                } else if (action === "unsubscribe") {
                    current.attr("disabled", true);
                    location.reload(true);
                } else if (action === "subscribe") {
                    current.attr("disabled", true);
                    location.reload(true);
                } else if (action === "read-all") {
                    current.attr("disabled", true);
                    var all_read_buttons = $('[data-action="read"]');
                    all_read_buttons.addClass("is-success is-selected");
                    all_read_buttons.data("action", "unread");
                }
            }
        }
    });

    return false;
}


function showEditTagsBox() {
    $('#show-tags-box').addClass("is-hidden");
    $('#edit-tags-box').removeClass("is-hidden");

}

$(function() {
    $('[data-action="star"]').click(star);
    $('[data-action="unstar"]').click(star);
    $('[data-action="read"]').click(star);
    $('[data-action="unread"]').click(star);
    $('[data-action="unsubscribe"]').click(star);
    $('[data-action="subscribe"]').click(star);
    $('[data-action="read-all"]').click(star);

    $('#edit-tags-button').click(showEditTagsBox);
});


$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
