function jump_to_detail(encodeed_prompt_raw) {
    gradioApp().querySelector('#tab_prompt_template').querySelectorAll('button')[1].click();
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