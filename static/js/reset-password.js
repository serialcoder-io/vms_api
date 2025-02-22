document.addEventListener("DOMContentLoaded", ()=>{
    const resetPwdForm = document.getElementById("reset-pwd-form")
    const passwordField = document.getElementById("password")
    const confirmPasswordField = document.getElementById("confirm-password")
    const regExPwd = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

    resetPwdForm.addEventListener("submit", (event)=>{
        event.preventDefault()
        if(passwordField.value.trim() !== confirmPasswordField.value.trim()){
            console.log("password missmatch")
            return;
        }
        if(!passwordField.value.trim().match(regExPwd)){
            console.log("password must have at least 8 characters, " +
                "including at least 1 capital letter, 1 lowercase letter, 1 digit and 1 special char ");
            return;
        }
        window.location.href = '/vms/auth/reset_password_success'
    })

})