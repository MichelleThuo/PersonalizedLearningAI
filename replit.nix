{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.ffmpeg
    pkgs.ffmpeg-full
    pkgs.postgresql
    pkgs.openssl
  ];
}
