;;; eklip.el -- Brief introduction here.

;; Author: Yang,Ying-chao <yingchao.yang@icloud.com>

;;; Commentary:

;;; Code:

(let ((p (open-network-stream "eklip" nil "127.0.0.1" 9999)))
  (set-process-filter p (lambda (proc msg)
                        (PDEBUG "OUTPUT:")
                        (PDEBUG "PROC: " proc)
                        (PDEBUG "MSG: " msg)))
  (set-process-sentinel p  (lambda (proc msg)
                          (PDEBUG "SENTINETL")
                          (PDEBUG "PROC: " proc)
                          (PDEBUG "MSG: " msg)))

  (process-send-string p "hhhh")
  (accept-process-output p)
  (process-send-string p "abcd")
  (accept-process-output p)
  (process-send-string p "hjuh")
  (accept-process-output p)
  (delete-process p)
  )

(provide 'eklip)

;; Local Variables:
;; coding: utf-8
;; indent-tabs-mode: nil
;; End:

;;; eklip.el ends here
