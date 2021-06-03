// JavaScript for index.html

// Setup page
$(document).ready(() => {

    // Load overlay images from database
    $.ajax({
        type: "GET",
        url: "/api/images",
        success: (res) => {
            res = JSON.parse(res)
            res.reverse();
            for (const row of res) {
                $('#images-div-inner').prepend(`
                    <button class="options-button flex column small-text overlay-image-button" style="background-position: center center; background-repeat: no-repeat;background-size: contain; background-image: url('data:image/png;base64,${row.image}')" id="${row.name}">${row.name}</button>
                `);
            }
        }
    });

    // Set target slider values
    $.ajax({
        type: "GET",
        url: "/api/tgt-hsv",
        success: (res) => {
            slider_values = res.split(' ').map(x=>parseInt(x));
            $('#hue-target').val(slider_values[0]);
            $('#saturation-target').val(slider_values[1]);
            $('#value-target').val(slider_values[2]);
        }
    });

    // Set variance slider values
    $.ajax({
        type: "GET",
        url: "/api/var-hsv",
        success: (res) => {
            slider_values = res.split(' ').map(x=>parseInt(x));
            $('#hue-variance').val(slider_values[0]);
            $('#saturation-variance').val(slider_values[1]);
            $('#value-variance').val(slider_values[2]);
        }
    });
});


// Bind overlay buttons (row 1) to functions

$(document).on('click', '.overlay-image-button', (e) => {
    $.ajax({
        type: "POST",
        url: `/api/overlay/image/${e.target.id}`
    });
});

$('#arrow-button').on('click', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/overlay/arrow"
    });
});

$('#save-button').on('click', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/overlay/save"
    });
});


// Bind option buttons (row 2) to functions

$('#overlays-button').on('click', (e) => {
    location.href='/overlays';
});

$('#gallery-button').on('click', (e) => {
    location.href='/gallery';
});

$('#reset-servos-button').on('click', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/reset-servos"
    });
});

$('#calibrate-button').on('click', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/calibrate"
    });
    $.ajax({
        type: "GET",
        url: "/api/tgt-hsv",
        success: (res) => {
            slider_values = res.split(' ').map(x=>parseInt(x));
            $('#hue-target').val(slider_values[0]);
            $('#saturation-target').val(slider_values[1]);
            $('#value-target').val(slider_values[2]);
        }
    });
});

$('#toggle-mask-button').on('click', (e) => {
    $('.stream').toggle();
});

$('#toggle-sliders-button').on('click', (e) => {
    let sliders_div_display = $('#sliders-div').css("display");
    if (sliders_div_display == "none") {
        $('#sliders-div').css("display", "flex");
    } else if (sliders_div_display == "flex") {
        $('#sliders-div').css("display", "none");
    }
});

$('#shutdown-button').on('click', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/shutdown"
    });
});

$('.target-slider').on('input', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/set-target",
        data: JSON.stringify({'element': $(e.target).attr('id').split('-')[0], 'value': $(e.target).val()}),
        dataType: 'json',
        contentType: 'application/json'
    });
});

$('.variance-slider').on('input', (e) => {
    $.ajax({
        type: "POST",
        url: "/api/set-variance",
        data: JSON.stringify({'element': $(e.target).attr('id').split('-')[0], 'value': $(e.target).val()}),
        dataType: 'json',
        contentType: 'application/json'
    });
});