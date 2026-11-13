# Bengali Book AI — কাজের তালিকা

শেষ আপডেট: 2026-11-13

এই ফাইলে বাস্তব কাজের অবস্থা রাখা হবে। যাচাই ছাড়া কোনো কাজ Done করা যাবে না।

## কোডে যুক্ত
- [x] Bengali ও English Tesseract OCR language package install এবং workflow-এ language verification.
- [x] Native PDF text quality কম হলে OCR fallback.
- [x] Tesseract PSM 6 ও PSM 11 ফল তুলনা করে text নির্বাচন.
- [x] Worker page batch upload-এ transient HTTP retry এবং accepted page count যাচাই.
- [x] OCR quality unit tests এবং Python syntax validation workflow-এ চালানো.

## যাচাই বাকি
- [ ] নতুন Index PDF workflow GitHub Actions-এ বাস্তবে সফলভাবে চালানো.
- [ ] আগে upload করা দুই PDF-এর প্রত্যেকটির Actions run, indexed page count এবং Worker book status পরীক্ষা করা.
- [ ] Bengali scanned PDF থেকে কয়েকটি page text হাতে যাচাই করা; matra, যুক্তাক্ষর, page order ও citation মিলিয়ে দেখা.
- [ ] Human-verified Bengali PDF OCR benchmark তৈরি করা.
- [ ] বড় ও mixed native-text/scanned PDF-এ runtime এবং memory পরীক্ষা করা.
- [ ] Production D1-এ indexed page count এবং ready status মিলিয়ে দেখা.

## নির্ভরতা / বাধা
- Repository secret WORKER_ADMIN_API_TOKEN সঠিক থাকতে হবে.
- GitHub Actions GITHUB_TOKEN-এর Contents write permission cover asset upload-এর জন্য প্রয়োজন.
- Cloudflare Worker এবং D1 production-এ সচল থাকতে হবে.
- OCR accuracy scan resolution, page skew, contrast, font ও language mix-এর ওপর নির্ভরশীল.
- বাস্তব PDF run না হওয়া পর্যন্ত production OCR verified বলা যাবে না.

## কাজের সীমা
- admin.html এবং soo.html এই OCR পরিবর্তনের অংশ নয়; আলাদা নির্দেশ ছাড়া পরিবর্তন করা হবে না.
- বইয়ের public-domain/open-license/permission অধিকার নিশ্চিত না হলে public indexing করা যাবে না.
- কোনো বাস্তব run ব্যর্থ হলে এখানে error, কারণ ও পরবর্তী পদক্ষেপ লিখতে হবে.
