;;; eklip.el -- Brief introduction here.

;; Author: Yang,Ying-chao <yingchao.yang@icloud.com>

;;; Commentary:

;;; Code:
(require 'bindat)

(defvar eklip--answer nil "Nil.")
(defvar eklip/server nil "Nil.")

(defun eklip--filter (proc msg)
  "Filter."
  (PDEBUG "OUTPUT:")
  (PDEBUG "PROC: " proc)
  (PDEBUG "MSG: " msg)
  ;; assume there is no message sent actively by server, and message is never splited...
  (push (string-make-unibyte msg) eklip--answer))

(defun eklip--send-to-server (query)
  "Send `QUERY' to server process `P', and return result."

  (unless eklip/server
    (error "Server is not setup"))

  (setq eklip--answer nil)
  (let* ((spec '((length u32)))
         (str (json-encode query))
         ret)
    (process-send-string eklip/server
                         (bindat-pack spec (list (cons 'length (length str)))))
    (process-send-string eklip/server str)

    (accept-process-output eklip/server)

    ;; parse result...

    (let ((yc/debug-log-limit -1))
      (PDEBUG "EKLIP--ANSWER: " (length eklip--answer)))

    (let* ((use-native-json (fboundp 'json-parse-string))
           (json-array-type 'list)
           (json-object-type 'hash-table)
           (json-false nil)
           (responses (nreverse eklip--answer))
           (unpacked (bindat-unpack spec (car responses)))
           (data-length (alist-get 'length unpacked)))

      (PDEBUG "DATA-LENGTH: " data-length)

      ;; modify first response, by removing first 4 bytes (length)...
      (setf (car responses) (substring (car responses) 4))

      ;; wait until all data is read, before parsing...

      (while (< (apply '+ (mapcar 'length responses))
                data-length)
        (setq eklip--answer nil)
        (PDEBUG "LEN1: " (length responses))
        (accept-process-output eklip/server)
        (setq responses (concat responses (nreverse eklip--answer)))
        (PDEBUG "LEN1: " (length responses)))

      (unless (= data-length (apply '+ (mapcar 'length responses)))
        (error "Not expected"))

      ;; Now start parsing...
      (if use-native-json
          (with-no-warnings
            (with-temp-buffer
              (json-parse-string str
                                 :object-type 'hash-table
                                 :null-object nil
                                 :false-object nil)))
        (setq ret (json-read-from-string (mapconcat 'identity responses "")))))

    (PDEBUG "QUERY: " query
      "\nRET: " ret)


    ;; check error....
    (aif (gethash "err" ret)
        (error "Query failed, %s" it))


    ret)
  )

(defun eklip/send-command (command result &rest args)
  "Send COMMAND to server, and return RESULT in response."
  (let* ((query (json-add-to-object (json-new-object) "cmd" command)))
    (when args
      (dolist (p args)
        (setq query (json-add-to-object query (car p) (cdr p)))))
    (gethash result (eklip--send-to-server query))))

(defvar eklip/book-list-window nil "Nil.")
(defvar eklip/clip-list-window nil "Nil.")

(defvar eklip/book-list-buffer nil "Book list buffer.")
(defvar eklip/clip-list-buffer nil "Clip list buffer of selected book.")

(defun eklip--setup-window (&optional clear)
  "Setup windows/buffers."
  (interactive)
  (set-window-dedicated-p (selected-window) nil)

  (when clear
    (dolist (fn '("eklip/books" "eklip/clips"))
      (aif (get-buffer fn)
          (kill-buffer it))))

  (setq eklip/book-list-buffer (get-buffer-create "eklip/books")
        eklip/clip-list-buffer (get-buffer-create "eklip/clips"))

  (switch-to-buffer eklip/clip-list-buffer)

  (delete-other-windows)

  (setq eklip/clip-list-window (selected-window)
        eklip/book-list-window (split-window nil nil 'left))

  (select-window eklip/book-list-window)
  (set-window-buffer eklip/book-list-window eklip/book-list-buffer)

  (enlarge-window
   (truncate (* -1 (* (- (/ 1.0 2 ) (/ 1.0 3 )) (window-size eklip/book-list-window t))))
   t))

(defun eklip/on-clip-activated (ov)
  "Callback when a clip is activated."
  (PDEBUG "OV: " ov)
  (let* ((clip-id (overlay-get ov 'ID))
         ;; (clips (eklip/send-command "get-clips" "clips" (cons "book-id" book-id)))
         )
    (PDEBUG "CLIP_ID: " clip-id)
    ))

(defun eklip/on-book-selected (ov)
  "Callback when a book is selected."
  (PDEBUG "OV: " ov)
  (let* ((book-id (overlay-get ov 'ID))
         (clips (eklip/send-command "get-clips" "clips" (cons "book-id" book-id))))
    (PDEBUG "BOOK_ID: " book-id)
    (let ((yc/debug-log-limit -1))
      (PDEBUG "CLIPS:" clips))

    (select-window eklip/clip-list-window)
    (erase-buffer)

    (dolist (clip clips)
      (let ((start (point)))
        (insert (concat "- " (cadr clip) "\n"))
        (let ((btn  (make-button start (1- (point))
                                 'action #'eklip/on-clip-activated)))
          (overlay-put btn 'ID (car clip))
          (overlay-put btn 'face 'default))))))

(defun eklip/fill-books ()
  "Query books from process `P' and fill into book-window."
  (let ((books (eklip/send-command "get-books" "books")))
    (PDEBUG "BOOKS: " books)
    (select-window eklip/book-list-window)
    (dolist (book books)
      (PDEBUG "   " book)
      ;; TODO: do not display full name if name is too long.
      (insert (concat "- " (cadr book) ))

      (let ((btn  (make-button (+ 2 (point-at-bol)) (point-at-eol)
                               'action #'eklip/on-book-selected)))
        (PDEBUG "BTN: " btn)
        (overlay-put btn 'ID (car book)))
      (insert "\n")
      )

    ;; todo: bind key: q to quit...

    )
  )

(defun eklip/setup-server ()
  "Description."
  ;; TODO: start klip-server...
  (setq eklip/server (open-network-stream "eklip" nil "127.0.0.1" 9999))
  (set-process-filter eklip/server #'eklip--filter)
  (set-process-sentinel eklip/server  (lambda (proc msg)
                             (PDEBUG "SENTINETL")
                             (PDEBUG "STAT: " msg)))
  )

(defun eklip/teardown-server ()
  "Tearndown server."
  (delete-process eklip/server)
  )

(let ()
  (eklip/teardown-server) ;; should be called before quiting...
  (eklip/setup-server)
  (eklip--setup-window t)
  (eklip/fill-books)
  )

(provide 'eklip)

;; Local Variables:
;; coding: utf-8
;; indent-tabs-mode: nil
;; End:

;;; eklip.el ends here
