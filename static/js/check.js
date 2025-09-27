function checkStudent(f){
    const sno = f.sno.value.trim();
    const sname = f.sname.value.trim();
    const pw = f.password.value;
    const pwc = f.password_check.value;

    if(!/^[0-9]+$/.test(sno)){
        alert("학번은 숫자만 입력해주세요.");
        f.sno.focus();
        return false;
    }
    if(!/^[가-힣A-Za-z0-9 ]+$/.test(sname)){
        alert("이름은 한글, 영어, 숫자, 공백만 가능합니다.");
        f.sname.focus();
        return false;
    }
    if(pw !== pwc){
        alert("비밀번호와 비밀번호 확인이 일치하지 않습니다.");
        f.password_check.focus();
        return false;
    }
    return true;
}