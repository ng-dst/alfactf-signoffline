function showPopup(message) {
    const popup = $('<div class="popup"></div>').text(message);
    $('body').append(popup);

    setTimeout(function() {
        popup.fadeOut(300, function() {
            $(this).remove();
        });
    }, 3000);
}
