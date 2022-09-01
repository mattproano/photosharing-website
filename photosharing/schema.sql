CREATE DATABASE IF NOT EXISTS photosharedemo;
USE photosharedemo;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(255),
    last_name varchar(255),
    dob date, 
    hometown varchar(255),
    gender varchar(255),
    activity int4,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends (	
	user_id int4,
	friend_id int4,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (friend_id) REFERENCES Users(user_id)
);

CREATE TABLE Albums
(	
	album_id int4 AUTO_INCREMENT NOT NULL,
	album_name varchar(255),
	user_id int4,
	start_date date,
	CONSTRAINT albums_pk PRIMARY KEY (album_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  album_id int4,
  imgdata longblob,
  likecount int4,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id)
  ON DELETE CASCADE
);

CREATE TABLE Tags
(
	tag_id int4 AUTO_INCREMENT NOT NULL,
	tag_text varchar(255),
	CONSTRAINT tag_pk PRIMARY KEY (tag_id)
);

CREATE TABLE PictureTags
(
	picture_id int4,
	tag_id int4,
	FOREIGN KEY (tag_id) REFERENCES Tags(tag_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Comments
(
	comment_id int4 AUTO_INCREMENT NOT NULL,
	comment_text varchar(255),
    user_id int4,
    picture_id int4,
	comment_date date,
	CONSTRAINT comments_pk PRIMARY KEY (comment_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE UserLikes
(
	user_id int4,
	picture_id int4,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');