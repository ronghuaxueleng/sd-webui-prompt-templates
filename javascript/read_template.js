
let black_overlay = document.getElementById('black_overlay');
let enlargeContainer = document.getElementById('enlargeContainer');
let closeBtn = document.getElementById('close');

let toEnlargeImg = document.querySelector('.toEnlargeImg');
toEnlargeImg.addEventListener('click', function () {
    // 获取当前图片的路径
    let imgUrl = this.src;
    // 显示黑色遮罩和预览容器
    black_overlay.style.display = 'block';
    enlargeContainer.style.display = 'block';
    let img = new Image();
    img.src = imgUrl;
    img.classList.add('enlargePreviewImg');
    if (closeBtn.nextElementSibling) {
        enlargeContainer.removeChild(closeBtn.nextElementSibling);
    }
    enlargeContainer.appendChild(img);
});

// 关闭预览
closeBtn.addEventListener('click', function () {
    black_overlay.style.display = 'none';
    enlargeContainer.style.display = 'none';
});

function delete_template(id) {
    if (confirm('确定要删除这个模版吗？')) {
        textarea = gradioApp().querySelector('#template_id textarea')
        textarea.value = id
        updateInput(textarea)
        textarea.click()
        gradioApp().querySelector('#delete_template_by_id_btn').click()
    }
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