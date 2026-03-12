use std::net::TcpListener;
use std::io::Write;

fn main() {
    let listener = TcpListener::bind("0.0.0.0:8080").unwrap();

    println!("Rust API running on port 8080");

    for stream in listener.incoming() {
        let mut stream = stream.unwrap();

        let response = "HTTP/1.1 200 OK\r\n\r\nSDD Navigator API";

        stream.write_all(response.as_bytes()).unwrap();
    }
}