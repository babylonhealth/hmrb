use std::os::raw::c_int;

#[no_mangle]
pub extern "C" fn is_prime(n: *const c_int) -> c_int {
    let n = n as i32;
    if n < 2 {
        return 0
    }
    for i in 2 .. n {
        if  n % i == 0 {
            return 0
        }
    }
    1
}

#[test]
fn test_is_prime() {
    let not_prime = 12;
    let is_a_prime = 13;
    let _true: c_int = 1;
    let _false: c_int = 0;
    assert_eq!(is_prime(not_prime as *const c_int), _false);
    assert_eq!(is_prime(is_a_prime as *const c_int), _true);
}
