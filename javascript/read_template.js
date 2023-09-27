"use strict";
let preview_init = function () {
    let prompt_template_image_preview_black_overlay_div = null;
    let prompt_template_image_preview_close_div = null;
    let prompt_template_image_preview_to_image = null;
    if (document.getElementById('prompt_template_image_preview_black_overlay') == null) {
        prompt_template_image_preview_black_overlay_div = document.createElement('div');
        prompt_template_image_preview_black_overlay_div.id = 'prompt_template_image_preview_black_overlay';
        document.body.append(prompt_template_image_preview_black_overlay_div);
        prompt_template_image_preview_close_div = document.createElement('div');
        prompt_template_image_preview_close_div.id = 'prompt_template_image_preview_close_enlargeContainer'
        prompt_template_image_preview_to_image = document.createElement('img');
        prompt_template_image_preview_to_image.id = "prompt_template_image_preview_to_image_close";
        prompt_template_image_preview_to_image.className = "prompt_template_image_preview_to_image_close";
        prompt_template_image_preview_to_image.src = "data:image/png;base64,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";
        prompt_template_image_preview_close_div.append(prompt_template_image_preview_to_image);
        document.body.append(prompt_template_image_preview_close_div);
    } else {
        prompt_template_image_preview_black_overlay_div = document.getElementById('prompt_template_image_preview_black_overlay');
        prompt_template_image_preview_close_div = document.getElementById('prompt_template_image_preview_close_enlargeContainer');
        prompt_template_image_preview_to_image = document.getElementById('prompt_template_image_preview_to_image_close');
    }

    let toEnlargeImgs = document.getElementsByClassName('prompt_template_image_preview_tolargeImg');

    for (let i = 0; i < toEnlargeImgs.length; i++) {
        let toEnlargeImg = toEnlargeImgs[i];
        toEnlargeImg.addEventListener('click', function () {
            // 获取当前图片的路径
            let imgUrl = this.src;
            // 显示黑色遮罩和预览容器
            prompt_template_image_preview_black_overlay_div.style.display = 'block';
            prompt_template_image_preview_close_div.style.display = 'block';
            let img = new Image();
            img.src = imgUrl;
            img.classList.add('prompt_template_image_preview_enlarge_previewimg');
            if (prompt_template_image_preview_to_image.nextElementSibling) {
                prompt_template_image_preview_close_div.removeChild(prompt_template_image_preview_to_image.nextElementSibling);
            }
            prompt_template_image_preview_close_div.appendChild(img);

            //绑定滚动事件
            img.onwheel = function (event) {
                const width = getComputedStyle(img).width.slice(0, -2);
                const height = getComputedStyle(img).height.slice(0, -2);

                if (event.deltaY > 0) {
                    //向上滚动放大
                    img.style.width = parseInt(width) * 1.1 + "px";
                    img.style.height = parseInt(height) * 1.1 + "px";
                } else if (event.deltaY < 0) {
                    //向下滚动缩小
                    img.style.width = parseInt(width) * 0.9 + "px";
                    img.style.height = parseInt(height) * 0.9 + "px";
                }
            }

        });
    }

    // 关闭预览
    prompt_template_image_preview_to_image.addEventListener('click', function () {
        prompt_template_image_preview_black_overlay_div.style.display = 'none';
        prompt_template_image_preview_close_div.style.display = 'none';
    });
}
onAfterUiUpdate(preview_init)

onUiLoaded(function () {
    //创建工作栏
    let toolbar = document.createElement("div");
    toolbar.className = "gr-block gr-box relative w-full border-solid border border-gray-200 gr-padded";

    let save_all_flow_to_template_btn = document.createElement("button");
    save_all_flow_to_template_btn.innerHTML = "🎆";
    save_all_flow_to_template_btn.className = "gr-button gr-button-lg gr-button-tool lg secondary gradio-button tool";
    save_all_flow_to_template_btn.style.border = "none";
    save_all_flow_to_template_btn.title = "保存流程到模板";
    toolbar.appendChild(save_all_flow_to_template_btn);
    let modelbar = gradioApp().getElementById("quicksettings");
    modelbar.appendChild(toolbar);
})

function delete_template(id) {
    if (confirm('确定要删除这个模版吗？')) {
        let textarea = gradioApp().querySelector('#template_id textarea')
        textarea.value = id
        updateInput(textarea)
        textarea.click()
        gradioApp().querySelector('#delete_template_by_id_btn').click()
    }
}

function jump_to_detail(encodeed_prompt_raw, filename) {
    gradioApp().querySelector('#tab_prompt_template #template_detail_tab').parentElement.querySelectorAll('button')[1].click();
    let textarea = gradioApp().querySelector('#prompt_detail_text textarea')
    textarea.value = encodeed_prompt_raw
    updateInput(textarea)
    let filename_textarea = gradioApp().querySelector('#prompt_detail_filename_text textarea')
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

function prompt_send_to(where, text) {
    let textarea = gradioApp().querySelector('#prompt_selected_text textarea')
    textarea.value = text
    updateInput(textarea)

    gradioApp().querySelector('#prompt_send_to_' + where).click()

    where === 'txt2img' ? switch_to_txt2img() : switch_to_img2img()
}