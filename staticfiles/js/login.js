document.addEventListener("DOMContentLoaded", ()=>{
    const signinButton = document.getElementById("signin-btn")
    const spinner = document.getElementById("spinner")
    const usernameField = document.getElementById("username")
    const passwordField = document.getElementById("password")
    signinButton.onclick = () =>{
        const username = usernameField.value.trim()
        const password = passwordField.value.trim()
        if (username && password){
            spinner.classList.remove("d-none")
            setTimeout(()=>{
                spinner.classList.add("d-none")
            }, 3000)
        }
    }
})