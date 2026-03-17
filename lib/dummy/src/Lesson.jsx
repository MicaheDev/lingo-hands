import { useEffect, useState } from "react";
import Scene from "./Scene";

/* Feedback alert component to use when user ompelte a quiz or lesson */
function FeedbackAlert({ feedback }) {
  return (
    <div
      style={{
        backgroundColor:
          feedback.show && feedback.type === "error" ? "#eb3e3e" : "#499e4f",
      }}
      className={`c-lesson__feedback ${
        feedback.show && feedback.show ? "activate" : ""
      }`}
    >
      {feedback.message}
    </div>
  );
}

/* Principal or main component with contain all logic and others components */
export default function Lesson() {
  /* React states or variables that tell React when to update the view */
  const [allLessons, setAllLessons] = useState([]); // here we save the data in json format about the lesson
  const [lessonsLength, setLessonsLength] = useState(0); // stores the size of the data (number of lessons in the level)
  const [currentIndex, setCurrentIndex] = useState(0); // the data is a list of lessons; the index of the current lesson in the list is stored here.
  const [currentLesson, setCurrentLesson] = useState(null); // stores the data for the particular lesson using the index and the data data[currentIndex]
  const [currentSign, setCurrentSign] = useState("mixamo.com"); // stores the identifier of the current ASL animation
  const [mistakes, setMistakes] = useState(0); // stores mistakes of the user
  const [hits, setHits] = useState(0); // stores success of the user
  const [lastId, setLastId] = useState(""); // stores the current index to avoid adding multiple errors or successes for the same lesson

  // store the test options in a random order
  const [shuffle, setShuffle] = useState([]);

  // Feedback alert dict
  const [feedback, setFeedback] = useState({
    message: "",
    type: "",
    show: false,
  });

  // input value for the lesson (the user writes the answer)
  const [inputValue, setInputValue] = useState("");
  // Select html tag with options for the questionnaires (the user must click on the answer)
  const [selectedOption, setSelectedOption] = useState("");

  /*
  the usage effect controls the component's lifecycle. In this case, 
  the usage effect performs some action before the component is rendered.
  */
  useEffect(() => {
    try {
      /*
    Here we retrieve JSON data from an HTML tag in the Jinja template

    <script type="application/json" id="lesson-json">
    {{ level_content | tojson | safe }}
    </script>
      */
      const element = document.getElementById("lesson-json");
      if (!element) return;

      // convert plain text to json
      const data = JSON.parse(element.textContent);

      // if the data exists and is not empty
      if (data && data.length > 0) {
        // Update variable or state data with all lessons and length
        setLessonsLength(data.length);
        setAllLessons(data);

        const lessonData = data[currentIndex];

        // if the especificl lesson exist and is not empty
        if (lessonData) {
          // update states
          setCurrentLesson(lessonData);
          setShuffle(
            shuffleArray([
              lessonData.option_a,
              lessonData.option_b,
              lessonData.option_c,
              lessonData.correct_option,
            ])
          );
          setCurrentSign(lessonData.sign_id || "mixamo.com");
        }
      }
    } catch (error) {
      console.error("error loading lesson data:", error);
    }
  }, []);

  // shuffle algorithm, I copy from google
  function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      // Pick a random index from 0 to i (inclusive)
      const j = Math.floor(Math.random() * (i + 1));

      // Swap elements array[i] and array[j] using array destructuring
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  // refresh function to switch to the next lessons
  function updatelesson() {
    // increment curretn index
    let index = currentIndex + 1;
    // select new Lesson using the new index
    let newLesson = allLessons[index];
    setCurrentIndex(index);
    setCurrentLesson(newLesson);
    setCurrentSign(newLesson.sign_id);

    // deletes entries and selections
    setInputValue("");
    setSelectedOption("");

    setShuffle(
      shuffleArray([
        newLesson.option_a,
        newLesson.option_b,
        newLesson.option_c,
        newLesson.correct_option,
      ])
    );
  }

  // Function to display the feedback or alert component for 1 second and then disappear
  function showFeedback({ message, type }) {
    setFeedback({ message, type, show: true });

    setTimeout(() => {
      setFeedback((prev) => {
        return { ...prev, show: false };
      });
    }, 1000);
  }

  // This is where the logic for verifying exams and lessons is used.
  function handleCheck() {
    // If step_type or mode is learn, we do this
    if (currentLesson.step_type === "learn") {
      // verify the input is not emty if not show alert with feedback
      if (inputValue.length <= 0) {
        showFeedback({ message: "Please, write the meaning", type: "error" });
        return;
      }

      // verify that the user input and the meaning are the same; if so, it is the correct answer
      if (inputValue.toLowerCase() === currentLesson.meaning) {
        showFeedback({ message: "Correct, good work!", type: "success" });

        /*
        Here we check if the user didn't advance to the next lesson because they answered incorrectly. 
        If they answered incorrectly before, they won't receive a hit for this lesson.
        */
        if (currentLesson.id !== lastId) {
          setHits(hits + 1);
          setLastId(currentLesson.id);
        }

        // update lesson
        updatelesson();
      } else {
        // if the answer is incorrect we show a feedback
        showFeedback({ message: "Incorrect, try again!", type: "error" });

        // here we check if the user answered incorrectly more than once
        // if it's the first error, we increment the mistakes state; otherwise, we do nothing.
        if (currentLesson.id !== lastId) {
          setMistakes(mistakes + 1);
          setLastId(currentLesson.id);
        }
      }
      // if the step type is "quiz" we do this
    } else {
      // it's the same as the "learn" mode
      if (selectedOption === currentLesson.correct_option) {
        showFeedback({ message: "Correct, good work!", type: "success" });
        if (currentLesson.id !== lastId) {
          setHits(hits + 1);
          setLastId(currentLesson.id);
        }

        updatelesson();
      } else {
        showFeedback({ message: "Incorrect, try again!", type: "error" });

        if (currentLesson.id !== lastId) {
          setMistakes(mistakes + 1);
          setLastId(currentLesson.id);
        }
      }
    }
  }

  // if there is no lesson, we apologize.
  if (!currentLesson) {
    return (
      <div className="c-lesson__container">
        <p>The content will be added soon.</p>
      </div>
    );
  }

  return (
    <div className="c-lesson__container">
      {/* Render feedback alert*/}
      <FeedbackAlert feedback={feedback} />
      {/* Render learn mode*/}
      {currentLesson.step_type === "learn" ? (
        <>
          <h1>Learn the sign</h1>
          <span className="c-lesson__mistakes">Mistakes: {mistakes}</span>
          <span className="c-lesson__hits">Hits: {hits}</span>

          {/* 3D scene with dummy */}
          <Scene signId={currentSign} />

          <div className="c-lesson-meaning__conatiner">
            <h3>Meaning:</h3>
            <p className="c-lesson__meaning">{currentLesson.meaning}</p>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleCheck();
            }}
          >
            <input
              autoFocus={true}
              autoComplete="off"
              type="text"
              value={inputValue}
              className="c-form__input"
              placeholder="Type the meaning here..."
              onChange={(e) => setInputValue(e.target.value)}
            />
          </form>
        </>
      ) : (
        <>
          {/* Render quiz mode*/}
          <h1>What is this sign?</h1>
          <span className="c-lesson__mistakes">Mistakes: {mistakes}</span>
          <span className="c-lesson__hits">Hits: {hits}</span>

          {/* 3D scene with dummy */}
          <Scene signId={currentSign} />

          <h3>Options:</h3>
          <div className="c-lesson__options">
            {/* the map is similar to the for loop in Python with Jinja; it iterates and plots elements of a list */}
            {shuffle.map((opt, index) => (
              <label
                key={index}
                className={`c-form__option-label ${
                  selectedOption === opt ? "is-selected" : ""
                }`}
                htmlFor={`option${index}`}
              >
                {opt}
                <input
                  type="radio"
                  value={opt}
                  name="option"
                  id={`option${index}`}
                  className="c-form__option-btn"
                  checked={selectedOption === opt} 
                  onChange={(e) => setSelectedOption(e.target.value)}
                />
              </label>
            ))}
          </div>
        </>
      )}
      {/* 
      If it's the last lesson, we replace the verification button with a form 
      containing an action that will send the information to a Python route to verify the level 
      */}
      {lessonsLength - 1 === currentIndex ? (
        <form action={`/lesson/${currentLesson.level_id}`} method="post">
          <input type="hidden" name="mistakes" value={mistakes} />
          <input type="hidden" name="lessons" value={lessonsLength} />
          <button type="submit" className="c-form__btn">
            Check
          </button>
        </form>
      ) : (
        <button onClick={handleCheck} className="c-form__btn">
          Check
        </button>
      )}
    </div>
  );
}
