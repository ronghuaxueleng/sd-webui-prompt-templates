function delete_template_onclick(id) {
    textarea = gradioApp().querySelector('#delete_template_id textarea')
    textarea.value = id
    updateInput(textarea)
    textarea.click()
    gradioApp().querySelector('#delete_template_id_btn').click()
}
function jump_to_detail(encodeed_prompt_raw, filename) {
    gradioApp().querySelector('#tab_prompt_template').querySelectorAll('button')[1].click();
    textarea = gradioApp().querySelector('#prompt_detail_text textarea')
    textarea.value = encodeed_prompt_raw
    updateInput(textarea)
    filename_textarea = gradioApp().querySelector('#prompt_detail_filename_text textarea')
    filename_textarea.value = filename
    updateInput(filename_textarea)
    textarea.click()
    gradioApp().querySelector('#prompt_detail_text_btn').click()
}
function prompt_send_to_txt2img(encodeed_prompt_raw) {
    prompt_send_to('txt2img', encodeed_prompt_raw)
}

function prompt_send_to_img2img(encodeed_prompt_raw) {
    prompt_send_to('img2img', encodeed_prompt_raw)
}

function prompt_send_to(where, text){
    textarea = gradioApp().querySelector('#prompt_selected_text textarea')
    textarea.value = text
    updateInput(textarea)

    gradioApp().querySelector('#prompt_send_to_'+where).click()

    where === 'txt2img' ? switch_to_txt2img() : switch_to_img2img()
}